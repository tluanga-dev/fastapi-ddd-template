from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr


class PermissionResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str
    permissions: List[PermissionResponse]


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    first_name: str
    last_name: str
    name: str
    role: Optional[RoleResponse]
    location_id: Optional[UUID]
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class TokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = "bearer"
