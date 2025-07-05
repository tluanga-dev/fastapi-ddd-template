#!/usr/bin/env python3
"""Create admin user for testing authentication"""

import asyncio
import os
import sys
from datetime import datetime
from uuid import uuid4

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_admin_user():
    """Create admin user with basic setup"""
    
    # Database URL
    db_url = "sqlite+aiosqlite:///./database.db"
    engine = create_async_engine(db_url)
    
    try:
        async with engine.begin() as conn:
            # Drop existing tables to recreate with correct schema
            await conn.execute(text("DROP TABLE IF EXISTS user_permissions"))
            await conn.execute(text("DROP TABLE IF EXISTS role_permissions"))
            await conn.execute(text("DROP TABLE IF EXISTS users"))
            await conn.execute(text("DROP TABLE IF EXISTS roles"))
            await conn.execute(text("DROP TABLE IF EXISTS permissions"))
            
            # Create users table with all columns
            await conn.execute(text("""
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    user_type TEXT DEFAULT 'USER',
                    is_superuser BOOLEAN DEFAULT 0,
                    location_id TEXT,
                    last_login TIMESTAMP,
                    role_id TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    updated_by TEXT
                );
            """))
            
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS roles (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    template TEXT,
                    is_system BOOLEAN DEFAULT 0,
                    can_be_deleted BOOLEAN DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    updated_by TEXT
                );
            """))
            
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS permissions (
                    id TEXT PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    updated_by TEXT
                );
            """))
            
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS role_permissions (
                    role_id TEXT,
                    permission_id TEXT,
                    FOREIGN KEY (role_id) REFERENCES roles(id),
                    FOREIGN KEY (permission_id) REFERENCES permissions(id)
                );
            """))
            
            # Create admin role
            admin_role_id = str(uuid4())
            await conn.execute(text("""
                INSERT OR IGNORE INTO roles (id, name, description, created_at, updated_at)
                VALUES (:id, :name, :description, :created_at, :updated_at)
            """), {
                "id": admin_role_id,
                "name": "ADMIN",
                "description": "System Administrator",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            # Create basic permissions
            permissions = [
                ("USER_VIEW", "View users"),
                ("USER_CREATE", "Create users"), 
                ("USER_UPDATE", "Update users"),
                ("USER_DELETE", "Delete users"),
                ("SALE_VIEW", "View sales"),
                ("RENTAL_VIEW", "View rentals"),
                ("INVENTORY_VIEW", "View inventory"),
                ("CUSTOMER_VIEW", "View customers"),
                ("SYSTEM_CONFIG", "System configuration")
            ]
            
            permission_ids = []
            for code, name in permissions:
                perm_id = str(uuid4())
                permission_ids.append(perm_id)
                await conn.execute(text("""
                    INSERT OR IGNORE INTO permissions (id, code, name, created_at, updated_at)
                    VALUES (:id, :code, :name, :created_at, :updated_at)
                """), {
                    "id": perm_id,
                    "code": code,
                    "name": name,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                
                # Assign permission to admin role
                await conn.execute(text("""
                    INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                    VALUES (:role_id, :permission_id)
                """), {
                    "role_id": admin_role_id,
                    "permission_id": perm_id
                })
            
            # Create admin user
            admin_user_id = str(uuid4())
            hashed_pwd = hash_password("admin123")
            
            await conn.execute(text("""
                INSERT OR REPLACE INTO users (
                    id, email, hashed_password, name, first_name, last_name, 
                    username, user_type, is_superuser, role_id, is_active, 
                    created_at, updated_at
                )
                VALUES (:id, :email, :hashed_password, :name, :first_name, :last_name, 
                        :username, :user_type, :is_superuser, :role_id, :is_active, 
                        :created_at, :updated_at)
            """), {
                "id": admin_user_id,
                "email": "admin@rental.com",
                "hashed_password": hashed_pwd,
                "name": "System Administrator",
                "first_name": "System",
                "last_name": "Administrator",
                "username": "admin",
                "user_type": "ADMIN",
                "is_superuser": True,
                "role_id": admin_role_id,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            print("✅ Admin user created successfully!")
            print("📧 Email: admin@rental.com")
            print("🔑 Password: admin123")
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_admin_user())