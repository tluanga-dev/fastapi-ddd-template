#!/usr/bin/env python3
"""Test authentication directly"""

import asyncio
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from src.domain.value_objects.email import Email
from src.core.security import verify_password

async def test_auth():
    """Test authentication process"""
    
    # Database URL
    db_url = "sqlite+aiosqlite:///./database.db"
    engine = create_async_engine(db_url)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Create repository
            user_repo = UserRepositoryImpl(session)
            
            # Try to get user by email
            email = Email("admin@rental.com")
            print(f"📧 Looking for user with email: {email.value}")
            
            try:
                user = await user_repo.get_by_email(email)
                if user:
                    print(f"✅ Found user: {user.name}")
                    print(f"   User type: {user.user_type.value}")
                    print(f"   Has role: {'Yes' if user.role else 'No'}")
                    if user.role:
                        print(f"   Role name: {user.role.name}")
                        print(f"   Role has {len(user.role.permissions)} permissions")
                    
                    # Test password
                    test_password = "admin123"
                    if verify_password(test_password, user.hashed_password):
                        print(f"✅ Password verification successful!")
                    else:
                        print(f"❌ Password verification failed!")
                        
                    # Test permission check
                    permissions = user.get_permissions()
                    print(f"✅ User has {len(permissions)} effective permissions")
                    
                else:
                    print("❌ User not found")
                    
            except Exception as e:
                print(f"❌ Error loading user: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_auth())