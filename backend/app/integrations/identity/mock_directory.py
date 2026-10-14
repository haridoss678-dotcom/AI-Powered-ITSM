"""
Sorim.AI — Mock Directory Integration  (integrations/identity/mock_directory.py)

Simulates Active Directory / LDAP account state and safe mock administrative actions.
"""

from __future__ import annotations

from typing import Any

from app.core.errors import AppError, ErrorCode
from app.repositories.users import get_user, update_user_mock_account


class MockDirectory:
    def get_account(self, db: Any, employee_id: str) -> dict[str, Any]:
        user = get_user(db, employee_id)
        if user is None:
            raise AppError(
                code=ErrorCode.EMPLOYEE_NOT_FOUND,
                message=f"Employee '{employee_id}' was not found in directory.",
                http_status=404,
            )
        return user.get("mock_account", {})

    def reset_password(self, db: Any, employee_id: str) -> bool:
        account = self.get_account(db, employee_id)
        if account.get("privileged", False):
            return False
        updated = update_user_mock_account(
            db,
            employee_id,
            {"account_status": "active"},
        )
        return updated is not None

    def unlock_account(self, db: Any, employee_id: str) -> bool:
        account = self.get_account(db, employee_id)
        if account.get("privileged", False):
            return False
        updated = update_user_mock_account(
            db,
            employee_id,
            {"account_status": "active"},
        )
        return updated is not None

    def restart_service(self, db: Any, employee_id: str) -> bool:
        return True

    def clear_cache(self, db: Any, employee_id: str) -> bool:
        return True

    def check_vpn_status(self, db: Any, employee_id: str) -> bool:
        return True

    def restart_application(self, db: Any, employee_id: str) -> bool:
        return True


_directory = MockDirectory()


def get_mock_directory() -> MockDirectory:
    return _directory
