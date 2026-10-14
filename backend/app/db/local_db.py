"""
Sorim.AI — High-Fidelity Local In-Memory Database Fallback  (db/local_db.py)

Provides full collection emulation, atomic find_and_modify, and transaction locking
for local development when MongoDB Atlas is temporarily unreachable or blocked by
IP Access List firewalls.
"""

from __future__ import annotations

import copy
import threading
from types import SimpleNamespace
from typing import Any

from app.repositories.users import _load_demo_users


class LocalCursor:
    def __init__(self, items: list[dict[str, Any]]) -> None:
        self.items = list(items)

    def sort(self, field: str, direction: int = 1) -> "LocalCursor":
        self.items = sorted(
            self.items,
            key=lambda x: str(x.get(field, "")),
            reverse=(direction == -1),
        )
        return self

    def skip(self, n: int) -> "LocalCursor":
        self.items = self.items[n:]
        return self

    def limit(self, n: int) -> "LocalCursor":
        self.items = self.items[:n]
        return self

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


class LocalCollection:
    def __init__(self, initial: list[dict[str, Any]] | None = None, db: Any = None) -> None:
        self.docs = list(initial or [])
        self.db = db

    def _notify(self) -> None:
        if self.db is not None and hasattr(self.db, "save_state"):
            self.db.save_state()

    def _match(self, doc: dict[str, Any], query: dict[str, Any]) -> bool:
        for key, value in query.items():
            if "." in key:
                current: Any = doc
                for part in key.split("."):
                    current = current.get(part, {}) if isinstance(current, dict) else {}
                if current != value:
                    return False
                continue
            if doc.get(key) != value:
                return False
        return True

    def insert_one(self, doc: dict[str, Any], session: Any = None) -> dict[str, Any]:
        self.docs.append(dict(doc))
        self._notify()
        return doc

    def insert_many(self, docs: list[dict[str, Any]]) -> None:
        self.docs.extend([dict(d) for d in docs])
        self._notify()

    def find_one(self, query: dict[str, Any] | None = None, session: Any = None) -> dict[str, Any] | None:
        query = query or {}
        for doc in self.docs:
            if self._match(doc, query):
                return dict(doc)
        return None

    def find(self, query: dict[str, Any] | None = None) -> LocalCursor:
        query = query or {}
        return LocalCursor([dict(doc) for doc in self.docs if self._match(doc, query)])

    def count_documents(self, query: dict[str, Any] | None = None) -> int:
        query = query or {}
        return sum(1 for doc in self.docs if self._match(doc, query))

    def update_one(self, query: dict[str, Any], update: dict[str, Any], session: Any = None) -> SimpleNamespace:
        doc = None
        for d in self.docs:
            if self._match(d, query):
                doc = d
                break
        if doc is None:
            return SimpleNamespace(matched_count=0)

        patch = update.get("$set", {})
        for key, value in patch.items():
            if "." in key:
                parent = doc
                parts = key.split(".")
                for part in parts[:-1]:
                    parent = parent.setdefault(part, {})
                parent[parts[-1]] = value
            else:
                doc[key] = value
        self._notify()
        return SimpleNamespace(matched_count=1)

    def find_one_and_update(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
        return_document: Any = None,
        session: Any = None,
    ) -> dict[str, Any] | None:
        doc = None
        for d in self.docs:
            if self._match(d, query):
                doc = d
                break
        if doc is None:
            if not upsert:
                return None
            doc = {"_id": query["_id"]}
            self.docs.append(doc)

        for key, value in update.get("$inc", {}).items():
            doc[key] = doc.get(key, 0) + value
        for key, value in update.get("$set", {}).items():
            doc[key] = value
        self._notify()
        return dict(doc)


class LocalSession:
    def __init__(self, database: "LocalDB") -> None:
        self.database = database

    def __enter__(self) -> "LocalSession":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> bool:
        return False

    def with_transaction(self, callback: Any) -> Any:
        with self.database._transaction_lock:
            snapshot = {
                name: copy.deepcopy(coll.docs)
                for name, coll in self.database._collections.items()
            }
            try:
                return callback(self)
            except Exception:
                for name, docs in snapshot.items():
                    self.database._collections[name].docs = docs
                raise


class LocalClient:
    def __init__(self, database: "LocalDB") -> None:
        self.database = database

    def start_session(self) -> LocalSession:
        return LocalSession(self.database)


class LocalDB:
    def __init__(self) -> None:
        import json
        from pathlib import Path

        self._state_file = Path(__file__).resolve().parents[3] / "data" / "local_db_state.json"

        try:
            demo_users = _load_demo_users()
        except Exception:
            demo_users = [
                {"_id": "EMP-001", "name": "Demo Employee One", "email": "emp001@example.test", "department": "Finance", "mock_account": {"account_status": "password_expired", "privileged": False}},
                {"_id": "EMP-002", "name": "Demo Employee Two", "email": "emp002@example.test", "department": "Operations", "mock_account": {"account_status": "active", "privileged": False}},
                {"_id": "EMP-003", "name": "Demo Employee Three", "email": "emp003@example.test", "department": "IT Systems", "mock_account": {"account_status": "active", "privileged": True}},
            ]

        self._collections: dict[str, LocalCollection] = {
            "users": LocalCollection(demo_users, db=self),
            "tickets": LocalCollection(db=self),
            "servicenow_mock_records": LocalCollection(db=self),
            "counters": LocalCollection(db=self),
            "audit_logs": LocalCollection(db=self),
            "chat_history": LocalCollection(db=self),
            "knowledge_metadata": LocalCollection(db=self),
            "automation_actions": LocalCollection(db=self),
            "software_requests": LocalCollection(db=self),
        }
        self._transaction_lock = threading.RLock()
        self.client = LocalClient(self)
        self._load_state()

    def save_state(self) -> None:
        try:
            import json
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            payload = {name: coll.docs for name, coll in self._collections.items()}
            self._state_file.write_text(json.dumps(payload, default=str, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_state(self) -> None:
        if self._state_file.exists():
            try:
                import json
                payload = json.loads(self._state_file.read_text(encoding="utf-8"))
                for name, docs in payload.items():
                    if name in self._collections and docs:
                        self._collections[name].docs = docs
            except Exception:
                pass

    def get_collection(self, name: str) -> LocalCollection:
        if name not in self._collections:
            self._collections[name] = LocalCollection(db=self)
        return self._collections[name]

    def __getitem__(self, name: str) -> LocalCollection:
        return self.get_collection(name)


_local_db_instance: LocalDB | None = None


def get_local_db() -> LocalDB:
    global _local_db_instance
    if _local_db_instance is None:
        _local_db_instance = LocalDB()
    return _local_db_instance
