from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

_DEMO_USERS_PATH = Path(__file__).resolve().parents[3] / "data" / "demo_users.json"
_REQUIRED_DEMO_USERS = {
    "EMP-001": ("password_expired", False),
    "EMP-002": ("active", False),
    "EMP-003": ("active", True),
}


def _validate_demo_users(users: Any) -> list[dict[str, Any]]:
    if not isinstance(users, list) or not users:
        raise RuntimeError("Demo user data must be a non-empty JSON array.")

    seen_ids: set[str] = set()
    users_by_id: dict[str, dict[str, Any]] = {}
    for index, user in enumerate(users, start=1):
        if not isinstance(user, dict):
            raise RuntimeError(f"Demo user entry {index} must be a JSON object.")

        employee_id = user.get("_id")
        if not isinstance(employee_id, str) or not employee_id.strip():
            raise RuntimeError(f"Demo user entry {index} must have a non-empty string _id.")
        if employee_id in seen_ids:
            raise RuntimeError(f"Demo user ID '{employee_id}' is duplicated.")
        seen_ids.add(employee_id)

        for field in ("name", "email", "department"):
            value = user.get(field)
            if not isinstance(value, str) or not value.strip():
                raise RuntimeError(
                    f"Demo user '{employee_id}' must have a non-empty string {field}."
                )

        account = user.get("mock_account")
        if not isinstance(account, dict):
            raise RuntimeError(f"Demo user '{employee_id}' must have a mock_account object.")
        account_status = account.get("account_status")
        if not isinstance(account_status, str) or account_status not in {
            "active",
            "locked",
            "password_expired",
        }:
            raise RuntimeError(f"Demo user '{employee_id}' has an invalid account_status.")
        if not isinstance(account.get("privileged"), bool):
            raise RuntimeError(f"Demo user '{employee_id}' must have a boolean privileged value.")

        created_at = user.get("created_at")
        if not isinstance(created_at, str):
            raise RuntimeError(f"Demo user '{employee_id}' must have an ISO timestamp created_at.")
        try:
            timestamp = datetime.fromisoformat(
                created_at[:-1] + "+00:00" if created_at.endswith("Z") else created_at
            )
        except ValueError as exc:
            raise RuntimeError(
                f"Demo user '{employee_id}' must have an ISO timestamp created_at."
            ) from exc
        if timestamp.tzinfo is None:
            raise RuntimeError(
                f"Demo user '{employee_id}' created_at must include a timezone."
            )

        users_by_id[employee_id] = user

    for employee_id, expected_account in _REQUIRED_DEMO_USERS.items():
        user = users_by_id.get(employee_id)
        if user is None:
            raise RuntimeError(f"Required demo employee '{employee_id}' is missing.")
        account = user["mock_account"]
        if (account["account_status"], account["privileged"]) != expected_account:
            raise RuntimeError(
                f"Required demo employee '{employee_id}' has an invalid mock account state."
            )

    return users


def _load_demo_users() -> list[dict[str, Any]]:
    try:
        contents = _DEMO_USERS_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError("Unable to read the demo user fixture.") from exc
    try:
        users = json.loads(contents)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The demo user fixture is not valid JSON.") from exc
    return _validate_demo_users(users)


def _collection(db: Any):
    if db is None:
        raise RuntimeError("MongoDB database handle is unavailable.")
    if hasattr(db, "get_collection"):
        collection = db.get_collection("users")
    elif hasattr(db, "__getitem__"):
        try:
            collection = db["users"]
        except KeyError as exc:
            raise RuntimeError("MongoDB collection 'users' is unavailable.") from exc
    else:
        raise RuntimeError("MongoDB collection 'users' is unavailable.")
    if collection is None:
        raise RuntimeError("MongoDB collection 'users' is unavailable.")
    return collection


def ensure_demo_users(db: Any) -> list[dict]:
    collection = _collection(db)
    if collection.count_documents({}) == 0:
        collection.insert_many(_load_demo_users())
    return list(collection.find({}).sort("_id", 1))


def get_user(db: Any, employee_id: str) -> Optional[dict]:
    collection = _collection(db)
    return collection.find_one({"_id": employee_id})


def update_user_mock_account(
    db: Any,
    employee_id: str,
    mock_account_patch: dict[str, Any],
    *,
    session: Any = None,
) -> dict[str, Any] | None:
    collection = _collection(db)
    options = {"session": session} if session is not None else {}
    update_fields = {f"mock_account.{k}": v for k, v in mock_account_patch.items()}
    collection.update_one({"_id": employee_id}, {"$set": update_fields}, **options)
    return collection.find_one({"_id": employee_id}, **options)


def list_users(db: Any) -> list[dict[str, Any]]:
    collection = _collection(db)
    if collection.count_documents({}) == 0:
        ensure_demo_users(db)
    return list(collection.find({}).sort("_id", 1))


def insert_user(db: Any, user_doc: dict[str, Any]) -> dict[str, Any]:
    collection = _collection(db)
    collection.insert_one(user_doc)
    return user_doc


