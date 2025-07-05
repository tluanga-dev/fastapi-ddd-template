#!/usr/bin/env python3
"""Test the actual login response format"""

import httpx
import json

# Test the login
response = httpx.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "email": "admin@rental.com",
        "password": "admin123"
    }
)

print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Content Type: {response.headers.get('content-type')}")
print(f"Raw Response: {response.text}")

if response.status_code == 200:
    try:
        data = response.json()
        print(f"\nParsed JSON: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"\nFailed to parse JSON: {e}")
else:
    print(f"\nError response")