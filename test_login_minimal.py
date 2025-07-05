#!/usr/bin/env python3
"""Minimal test to debug login"""

import asyncio
import os
import sys
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from src.domain.value_objects.email import Email
from src.core.security import verify_password, create_access_token, create_refresh_token
from datetime import timedelta

async def test_login_flow():
    """Test the login flow step by step"""
    
    # Database URL
    db_url = "sqlite+aiosqlite:///./database.db"
    engine = create_async_engine(db_url)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # 1. Get user
            user_repo = UserRepositoryImpl(session)
            email = Email("admin@rental.com")
            print(f"1. Looking for user: {email.value}")
            
            user = await user_repo.get_by_email(email)
            if not user:
                print("❌ User not found")
                return
                
            print(f"✅ User found: {user.name}")
            
            # 2. Verify password
            print(f"\n2. Verifying password...")
            if not verify_password("admin123", user.hashed_password):
                print("❌ Password verification failed")
                return
                
            print("✅ Password verified")
            
            # 3. Get permissions
            print(f"\n3. Getting permissions...")
            try:
                permissions = list(user.get_permissions())
                print(f"✅ Permissions: {len(permissions)} found")
            except Exception as e:
                print(f"❌ Error getting permissions: {e}")
                permissions = []
            
            # 4. Create access token
            print(f"\n4. Creating access token...")
            try:
                access_token_data = {
                    "sub": user.email.value,
                    "user_id": str(user.id),
                    "permissions": permissions
                }
                access_token = create_access_token(
                    data=access_token_data,
                    expires_delta=timedelta(minutes=30)
                )
                print(f"✅ Access token created: {access_token[:50]}...")
            except Exception as e:
                print(f"❌ Error creating access token: {e}")
                import traceback
                traceback.print_exc()
                
            # 5. Create response data
            print(f"\n5. Creating response...")
            try:
                response = {
                    "user": {
                        "id": str(user.id),
                        "email": user.email.value,
                        "name": user.name,
                        "user_type": user.user_type.value,
                        "is_superuser": user.is_superuser,
                    },
                    "access_token": access_token,
                    "token_type": "bearer"
                }
                print("✅ Response created successfully")
                print(f"   User Type: {user.user_type.value}")
                print(f"   Is Superuser: {user.is_superuser}")
            except Exception as e:
                print(f"❌ Error creating response: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_login_flow())