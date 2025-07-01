from typing import Optional
from uuid import UUID
from datetime import datetime

from src.domain.entities.base import BaseEntity
from src.domain.value_objects.email import Email


class User(BaseEntity):
    def __init__(
        self,
        email: Email,
        name: str,
        hashed_password: str,
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
        self.is_superuser = is_superuser

    def update_email(self, email: Email, updated_by: Optional[str] = None):
        self.email = email
        self.update_timestamp(updated_by)

    def update_name(self, name: str, updated_by: Optional[str] = None):
        self.name = name
        self.update_timestamp(updated_by)

    def update_password(self, hashed_password: str, updated_by: Optional[str] = None):
        self.hashed_password = hashed_password
        self.update_timestamp(updated_by)

    def make_superuser(self, updated_by: Optional[str] = None):
        self.is_superuser = True
        self.update_timestamp(updated_by)

    def revoke_superuser(self, updated_by: Optional[str] = None):
        self.is_superuser = False
        self.update_timestamp(updated_by)