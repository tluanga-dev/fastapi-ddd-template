from sqlalchemy import Column, String, Boolean, UUID, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
import uuid

from src.infrastructure.database.database import Base
from src.infrastructure.models.base import BaseModel


# Association table for role-permission many-to-many relationship
role_permission_association = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID, ForeignKey('roles.id')),
    Column('permission_id', UUID, ForeignKey('permissions.id'))
)


class PermissionModel(Base, BaseModel):
    __tablename__ = "permissions"

    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String)


class RoleModel(Base, BaseModel):
    __tablename__ = "roles"

    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String)
    
    # Many-to-many relationship with permissions
    permissions = relationship(
        "PermissionModel",
        secondary=role_permission_association,
        backref="roles"
    )
    
    # One-to-many relationship with users
    users = relationship("UserModel", back_populates="role")


# Update the existing user model to include role relationship
class UserModel(Base, BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Additional fields for JWT compatibility
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String, unique=True, index=True)
    location_id = Column(UUID)
    last_login = Column(DateTime)
    
    # Foreign key to role
    role_id = Column(UUID, ForeignKey('roles.id'), nullable=True)
    
    # Relationship with role
    role = relationship("RoleModel", back_populates="users")
