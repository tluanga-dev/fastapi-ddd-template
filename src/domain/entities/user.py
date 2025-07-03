from typing import Optional
from uuid import UUID
from datetime import datetime

from src.domain.entities.base import BaseEntity
from src.domain.entities.role import Role
from src.domain.value_objects.email import Email


class User(BaseEntity):
    def __init__(
        self,
        email: Email,
        name: str,
        hashed_password: str,
        role: Optional[Role] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        location_id: Optional[UUID] = None,
        last_login: Optional[datetime] = None,
        is_superuser: bool = False,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        is_active: bool = True,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
    ):
        super().__init__(id, created_at, updated_at, is_active, created_by, updated_by)
        self.email = email
        self.name = name
        self.hashed_password = hashed_password
        self.role = role
        self.first_name = first_name or name.split()[0] if name else ""
        self.last_name = last_name or " ".join(name.split()[1:]) if name and len(name.split()) > 1 else ""
        self.username = username or email.value
        self.location_id = location_id
        self.last_login = last_login
        self.is_superuser = is_superuser

    def update_email(self, email: Email, updated_by: Optional[str] = None):
        self.email = email
        self.update_timestamp(updated_by)

    def update_name(self, name: str, updated_by: Optional[str] = None):
        self.name = name
        self.first_name = name.split()[0] if name else ""
        self.last_name = " ".join(name.split()[1:]) if name and len(name.split()) > 1 else ""
        self.update_timestamp(updated_by)

    def update_password(self, hashed_password: str, updated_by: Optional[str] = None):
        self.hashed_password = hashed_password
        self.update_timestamp(updated_by)

    def assign_role(self, role: Role, updated_by: Optional[str] = None):
        self.role = role
        self.update_timestamp(updated_by)

    def update_last_login(self, login_time: datetime, updated_by: Optional[str] = None):
        self.last_login = login_time
        self.update_timestamp(updated_by)

    def make_superuser(self, updated_by: Optional[str] = None):
        self.is_superuser = True
        self.update_timestamp(updated_by)

    def revoke_superuser(self, updated_by: Optional[str] = None):
        self.is_superuser = False
        self.update_timestamp(updated_by)

    def has_permission(self, permission_code: str) -> bool:
        if self.is_superuser:
            return True
        if self.role:
            return self.role.has_permission(permission_code)
        return False

    def get_permissions(self) -> list[str]:
        if not self.role:
            return []
        return [perm.code for perm in self.role.permissions]