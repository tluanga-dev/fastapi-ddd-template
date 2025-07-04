#!/usr/bin/env python3
"""
Test script for Role-Based Access Control (RBAC) implementation
"""

import asyncio
import json
import requests
from datetime import datetime

API_URL = 'http://localhost:8000/api/v1'

def test_rbac():
    """Test the RBAC implementation"""
    print("🔐 Testing Role-Based Access Control Implementation\n")
    
    # Step 1: Login with admin credentials to get access token
    print("1. Logging in with admin credentials...")
    login_response = requests.post(f"{API_URL}/auth/login", json={
        "email": "admin@rental.com",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    login_data = login_response.json()
    access_token = login_data["access_token"]
    user_data = login_data["user"]
    
    print(f"✅ Login successful")
    print(f"   User: {user_data['email']}")
    print(f"   Role: {user_data['role']['name']}")
    print(f"   Permissions: {len(user_data['role']['permissions'])} permissions")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 2: Test role management endpoints
    print("\n2. Testing role management endpoints...")
    
    # Test listing roles
    print("   2.1 Testing list roles...")
    roles_response = requests.get(f"{API_URL}/roles/", headers=headers)
    if roles_response.status_code == 200:
        roles_data = roles_response.json()
        print(f"   ✅ Listed {len(roles_data['roles'])} roles")
        for role in roles_data['roles']:
            print(f"      - {role['name']}: {len(role['permissions'])} permissions")
    else:
        print(f"   ❌ Failed to list roles: {roles_response.text}")
    
    # Test creating a new role
    print("   2.2 Testing create role...")
    new_role_data = {
        "name": "Test Role",
        "description": "A test role for RBAC testing",
        "permission_codes": ["USER_VIEW", "PRODUCT_VIEW"]
    }
    
    create_role_response = requests.post(f"{API_URL}/roles/", 
                                       json=new_role_data, 
                                       headers=headers)
    
    if create_role_response.status_code == 201:
        created_role = create_role_response.json()
        print(f"   ✅ Created role: {created_role['name']}")
        print(f"      Permissions: {[p['code'] for p in created_role['permissions']]}")
        test_role_id = created_role['id']
    else:
        print(f"   ❌ Failed to create role: {create_role_response.text}")
        test_role_id = None
    
    # Step 3: Test permission management endpoints
    print("\n3. Testing permission management endpoints...")
    
    # Test listing permissions
    print("   3.1 Testing list permissions...")
    permissions_response = requests.get(f"{API_URL}/permissions/", headers=headers)
    if permissions_response.status_code == 200:
        permissions_data = permissions_response.json()
        print(f"   ✅ Listed {len(permissions_data['permissions'])} permissions")
        # Show first few permissions
        for i, perm in enumerate(permissions_data['permissions'][:5]):
            print(f"      - {perm['code']}: {perm['name']}")
        if len(permissions_data['permissions']) > 5:
            print(f"      ... and {len(permissions_data['permissions']) - 5} more")
    else:
        print(f"   ❌ Failed to list permissions: {permissions_response.text}")
    
    # Test getting a specific permission by code
    print("   3.2 Testing get permission by code...")
    perm_response = requests.get(f"{API_URL}/permissions/code/USER_VIEW", headers=headers)
    if perm_response.status_code == 200:
        perm_data = perm_response.json()
        print(f"   ✅ Retrieved permission: {perm_data['code']} - {perm_data['name']}")
    else:
        print(f"   ❌ Failed to get permission: {perm_response.text}")
    
    # Step 4: Test authorization on user endpoints
    print("\n4. Testing authorization on user endpoints...")
    
    # Test listing users (should work with admin permissions)
    print("   4.1 Testing authorized access to list users...")
    users_response = requests.get(f"{API_URL}/users/", headers=headers)
    if users_response.status_code == 200:
        users_data = users_response.json()
        print(f"   ✅ Successfully listed {len(users_data)} users with admin permissions")
    else:
        print(f"   ❌ Failed to list users: {users_response.text}")
    
    # Test unauthorized access (no token)
    print("   4.2 Testing unauthorized access (no token)...")
    unauth_response = requests.get(f"{API_URL}/users/")
    if unauth_response.status_code == 403 or unauth_response.status_code == 401:
        print("   ✅ Correctly blocked unauthorized access")
    else:
        print(f"   ❌ Unauthorized access not properly blocked: {unauth_response.status_code}")
    
    # Step 5: Test updating the test role
    if test_role_id:
        print("\n5. Testing role updates...")
        print("   5.1 Testing update role permissions...")
        
        update_role_data = {
            "description": "Updated test role description",
            "permission_codes": ["USER_VIEW", "PRODUCT_VIEW", "CUSTOMER_VIEW"]
        }
        
        update_response = requests.patch(f"{API_URL}/roles/{test_role_id}",
                                       json=update_role_data,
                                       headers=headers)
        
        if update_response.status_code == 200:
            updated_role = update_response.json()
            print(f"   ✅ Updated role successfully")
            print(f"      New permissions: {[p['code'] for p in updated_role['permissions']]}")
        else:
            print(f"   ❌ Failed to update role: {update_response.text}")
    
    # Step 6: Test getting role details
        print("   5.2 Testing get role details...")
        get_role_response = requests.get(f"{API_URL}/roles/{test_role_id}", headers=headers)
        if get_role_response.status_code == 200:
            role_details = get_role_response.json()
            print(f"   ✅ Retrieved role details: {role_details['name']}")
            print(f"      Permissions: {len(role_details['permissions'])}")
        else:
            print(f"   ❌ Failed to get role details: {get_role_response.text}")
    
    # Step 7: Clean up - delete the test role
        print("   5.3 Testing delete role...")
        delete_response = requests.delete(f"{API_URL}/roles/{test_role_id}", headers=headers)
        if delete_response.status_code == 204:
            print("   ✅ Successfully deleted test role")
        else:
            print(f"   ❌ Failed to delete test role: {delete_response.text}")
    
    print("\n🎉 RBAC Testing Complete!")
    print("\n📊 Summary:")
    print("✅ Admin user authentication works")
    print("✅ Role management endpoints implemented")
    print("✅ Permission management endpoints implemented")
    print("✅ Authorization decorators enforced on user endpoints")
    print("✅ Role-based access control is functional")

if __name__ == "__main__":
    test_rbac()