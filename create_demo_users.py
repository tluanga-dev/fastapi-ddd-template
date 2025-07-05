#!/usr/bin/env python3
"""
Create demo users for manager and staff roles
"""

import asyncio
import sys
import logging
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from src.core.config import settings
    from src.infrastructure.database import get_session
    from src.infrastructure.models.user import User as UserModel
    from src.infrastructure.models.role import Role as RoleModel
    from src.core.security import get_password_hash
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from uuid import uuid4
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running this from the project root with poetry")
    sys.exit(1)


async def get_or_create_role(session: AsyncSession, role_name: str) -> Optional[str]:
    """Get role ID by name, return None if not found"""
    try:
        result = await session.execute(
            select(RoleModel).where(RoleModel.name == role_name)
        )
        role = result.scalar_one_or_none()
        if role:
            return role.id
        else:
            logger.warning(f"Role '{role_name}' not found")
            return None
    except Exception as e:
        logger.error(f"Error getting role {role_name}: {e}")
        return None


async def user_exists(session: AsyncSession, email: str) -> bool:
    """Check if user with given email already exists"""
    try:
        result = await session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        user = result.scalar_one_or_none()
        return user is not None
    except Exception as e:
        logger.error(f"Error checking if user exists: {e}")
        return True  # Assume exists to avoid duplicates


async def create_demo_user(session: AsyncSession, email: str, name: str, role_name: str, password: str = "admin123") -> bool:
    """Create a demo user with specified role"""
    try:
        # Check if user already exists
        if await user_exists(session, email):
            logger.info(f"User {email} already exists, skipping...")
            return True
        
        # Get role ID
        role_id = await get_or_create_role(session, role_name)
        if not role_id:
            logger.error(f"Cannot create user {email} - role {role_name} not found")
            return False
        
        # Create user
        hashed_password = get_password_hash(password)
        user = UserModel(
            id=str(uuid4()),
            email=email,
            name=name,
            hashed_password=hashed_password,
            is_superuser=False,
            user_type="INTERNAL",
            first_name=name.split()[0] if ' ' in name else name,
            last_name=name.split()[1] if ' ' in name else "",
            username=email.split('@')[0],
            role_id=role_id,
            is_active=True
        )
        
        session.add(user)
        await session.commit()
        
        logger.info(f"✅ Created demo user: {email} with role {role_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create user {email}: {e}")
        await session.rollback()
        return False


async def create_demo_users():
    """Create demo users for testing"""
    logger.info("🚀 Creating demo users...")
    
    async for session in get_session():
        try:
            # Create demo users
            users_to_create = [
                {
                    "email": "manager@rental.com",
                    "name": "Demo Manager",
                    "role_name": "MANAGER",
                    "password": "manager123"
                },
                {
                    "email": "staff@rental.com", 
                    "name": "Demo Staff",
                    "role_name": "STAFF",
                    "password": "staff123"
                }
            ]
            
            success_count = 0
            for user_data in users_to_create:
                if await create_demo_user(session, **user_data):
                    success_count += 1
            
            logger.info(f"✅ Successfully created {success_count}/{len(users_to_create)} demo users")
            
            # List all users for verification
            logger.info("📋 Current users in database:")
            result = await session.execute(select(UserModel.email, UserModel.name, RoleModel.name.label('role_name'))
                                         .join(RoleModel, UserModel.role_id == RoleModel.id))
            users = result.all()
            
            for user in users:
                logger.info(f"   • {user.email} - {user.name} ({user.role_name})")
                
        except Exception as e:
            logger.error(f"Error in create_demo_users: {e}")
            await session.rollback()
            
        break  # Only use first session


if __name__ == "__main__":
    asyncio.run(create_demo_users())