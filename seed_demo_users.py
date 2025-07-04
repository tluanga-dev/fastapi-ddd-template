#!/usr/bin/env python3
"""
Database seeding script for demo users
Creates demo users with credentials from demo_credentials.md
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from src.infrastructure.database.session import get_db
from src.infrastructure.models.auth_models import UserModel, RoleModel, PermissionModel
from src.infrastructure.database import engine, Base
from src.domain.value_objects.email import Email


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


async def create_demo_permissions():
    """Create demo permissions"""
    permissions = [
        {"code": "user:read", "name": "Read Users", "description": "Can read user information"},
        {"code": "user:write", "name": "Write Users", "description": "Can create and update users"},
        {"code": "user:delete", "name": "Delete Users", "description": "Can delete users"},
        {"code": "category:read", "name": "Read Categories", "description": "Can read categories"},
        {"code": "category:write", "name": "Write Categories", "description": "Can create and update categories"},
        {"code": "category:delete", "name": "Delete Categories", "description": "Can delete categories"},
        {"code": "rental:read", "name": "Read Rentals", "description": "Can read rental information"},
        {"code": "rental:write", "name": "Write Rentals", "description": "Can create and update rentals"},
        {"code": "rental:delete", "name": "Delete Rentals", "description": "Can delete rentals"},
        {"code": "admin:all", "name": "Admin All", "description": "Full administrative access"},
    ]
    
    permission_objects = []
    async with AsyncSession(engine) as session:
        for perm_data in permissions:
            # Check if permission already exists using proper query
            result = await session.execute(
                select(PermissionModel).where(PermissionModel.code == perm_data["code"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                permission = PermissionModel(**perm_data)
                session.add(permission)
                permission_objects.append(permission)
                print(f"✅ Created permission: {perm_data['code']}")
            else:
                print(f"🔑 Permission already exists: {perm_data['code']}")
        
        await session.commit()
        
        # Return all permissions for role creation
        result = await session.execute(select(PermissionModel))
        return result.scalars().all()


async def create_demo_roles(permissions):
    """Create demo roles with permissions"""
    roles_data = [
        {
            "name": "admin",
            "description": "Administrator with full access",
            "permission_codes": ["admin:all", "user:read", "user:write", "user:delete", 
                               "category:read", "category:write", "category:delete",
                               "rental:read", "rental:write", "rental:delete"]
        },
        {
            "name": "manager", 
            "description": "Manager with limited administrative access",
            "permission_codes": ["user:read", "category:read", "category:write",
                               "rental:read", "rental:write"]
        },
        {
            "name": "staff",
            "description": "Staff with basic access",
            "permission_codes": ["category:read", "rental:read", "rental:write"]
        }
    ]
    
    # Create permission lookup
    perm_lookup = {p.code: p for p in permissions}
    
    role_objects = {}
    async with AsyncSession(engine) as session:
        for role_data in roles_data:
            # Check if role already exists
            result = await session.execute(
                select(RoleModel).where(RoleModel.name == role_data["name"])
            )
            existing_role = result.scalar_one_or_none()
            
            if not existing_role:
                role = RoleModel(
                    name=role_data["name"],
                    description=role_data["description"]
                )
                
                # Add permissions to role
                role_permissions = []
                for perm_code in role_data["permission_codes"]:
                    if perm_code in perm_lookup:
                        role_permissions.append(perm_lookup[perm_code])
                
                role.permissions = role_permissions
                session.add(role)
                role_objects[role_data["name"]] = role
            else:
                role_objects[role_data["name"]] = existing_role
        
        await session.commit()
        return role_objects


async def create_demo_users(roles):
    """Create demo users with credentials from demo_credentials.md"""
    
    # Demo credentials from demo_credentials.md
    demo_users = [
        {
            "email": "admin@rental.com",
            "password": "admin123",
            "name": "Demo Admin",
            "first_name": "Demo",
            "last_name": "Admin",
            "username": "admin",
            "is_superuser": True,
            "role": "admin"
        }
    ]
    
    async with AsyncSession(engine) as session:
        for user_data in demo_users:
            # Check if user already exists
            result = await session.execute(
                select(UserModel).where(UserModel.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                hashed_password = hash_password(user_data["password"])
                
                user = UserModel(
                    email=user_data["email"],
                    name=user_data["name"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    username=user_data["username"],
                    hashed_password=hashed_password,
                    is_superuser=user_data["is_superuser"],
                    role=roles[user_data["role"]]
                )
                
                session.add(user)
                print(f"✅ Created demo user: {user_data['email']}")
            else:
                print(f"👤 Demo user already exists: {user_data['email']}")
        
        await session.commit()


async def seed_database():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created/verified")
        
        # Create permissions
        print("🔑 Creating permissions...")
        permissions = await create_demo_permissions()
        print(f"✅ Created {len(permissions)} permissions")
        
        # Create roles
        print("👥 Creating roles...")
        roles = await create_demo_roles(permissions)
        print(f"✅ Created {len(roles)} roles")
        
        # Create demo users
        print("👤 Creating demo users...")
        await create_demo_users(roles)
        
        print("🎉 Database seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_database())
