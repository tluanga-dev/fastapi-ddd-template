#!/usr/bin/env python3
"""Test login API endpoint directly"""

import asyncio
import httpx

async def test_login():
    """Test the login endpoint"""
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                json={
                    "email": "admin@rental.com",
                    "password": "admin123"
                }
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Login successful!")
                print(f"User: {data['user']['name']}")
                print(f"Email: {data['user']['email']}")
                print(f"User Type: {data['user']['user_type']}")
                print(f"Access Token: {data['access_token'][:50]}...")
            else:
                print(f"\n❌ Login failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())