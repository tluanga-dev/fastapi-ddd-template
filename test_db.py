#!/usr/bin/env python3
"""Test database connection and user loading"""

import asyncio
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

async def test_db():
    """Test database connection"""
    
    # Database URL
    db_url = "sqlite+aiosqlite:///./database.db"
    engine = create_async_engine(db_url)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Test raw query
            result = await session.execute(text("SELECT * FROM users WHERE email = :email"), {"email": "admin@rental.com"})
            user_row = result.fetchone()
            
            if user_row:
                print("✅ Found user in database:")
                print(f"   ID: {user_row[0]}")
                print(f"   Email: {user_row[1]}")
                print(f"   Has password: {'Yes' if user_row[2] else 'No'}")
                print(f"   Name: {user_row[3] if len(user_row) > 3 else 'N/A'}")
                
                # Check columns
                result = await session.execute(text("PRAGMA table_info(users)"))
                columns = result.fetchall()
                print("\n📋 User table columns:")
                for col in columns:
                    print(f"   - {col[1]} ({col[2]})")
                    
                # Check role
                result = await session.execute(text("""
                    SELECT r.* FROM roles r 
                    JOIN users u ON u.role_id = r.id 
                    WHERE u.email = :email
                """), {"email": "admin@rental.com"})
                role_row = result.fetchone()
                
                if role_row:
                    print(f"\n✅ User has role: {role_row[1]}")
                else:
                    print("\n❌ User has no role assigned")
                    
            else:
                print("❌ No user found with email admin@rental.com")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_db())