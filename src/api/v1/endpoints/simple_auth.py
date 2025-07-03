"""Simple authentication endpoint for demo purposes"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

# Simple JWT functionality without dependencies
import json
import base64
from datetime import datetime

router = APIRouter()

# Demo users data
DEMO_USERS = {
    "admin@example.com": {
        "id": "1",
        "email": "admin@example.com",
        "username": "admin",
        "firstName": "Admin",
        "lastName": "User",
        "name": "Admin User",
        "password": "admin123",  # In production, this would be hashed
        "role": {
            "id": "1",
            "name": "Administrator",
            "description": "Full system access",
            "permissions": [
                {"id": "1", "code": "SALE_CREATE", "type": "SALE_CREATE", "description": "Create sales"},
                {"id": "2", "code": "SALE_VIEW", "type": "SALE_VIEW", "description": "View sales"},
                {"id": "3", "code": "RENTAL_CREATE", "type": "RENTAL_CREATE", "description": "Create rentals"},
                {"id": "4", "code": "RENTAL_VIEW", "type": "RENTAL_VIEW", "description": "View rentals"},
                {"id": "5", "code": "CUSTOMER_CREATE", "type": "CUSTOMER_CREATE", "description": "Create customers"},
                {"id": "6", "code": "CUSTOMER_VIEW", "type": "CUSTOMER_VIEW", "description": "View customers"},
                {"id": "7", "code": "INVENTORY_VIEW", "type": "INVENTORY_VIEW", "description": "View inventory"},
                {"id": "8", "code": "REPORT_VIEW", "type": "REPORT_VIEW", "description": "View reports"},
                {"id": "9", "code": "SYSTEM_CONFIG", "type": "SYSTEM_CONFIG", "description": "System configuration"},
            ]
        },
        "isActive": True,
        "createdAt": "2025-01-01T00:00:00Z"
    },
    "manager@example.com": {
        "id": "2",
        "email": "manager@example.com",
        "username": "manager",
        "firstName": "Manager",
        "lastName": "User",
        "name": "Manager User",
        "password": "manager123",
        "role": {
            "id": "2",
            "name": "Manager",
            "description": "Management access",
            "permissions": [
                {"id": "1", "code": "SALE_CREATE", "type": "SALE_CREATE", "description": "Create sales"},
                {"id": "2", "code": "SALE_VIEW", "type": "SALE_VIEW", "description": "View sales"},
                {"id": "3", "code": "RENTAL_CREATE", "type": "RENTAL_CREATE", "description": "Create rentals"},
                {"id": "4", "code": "RENTAL_VIEW", "type": "RENTAL_VIEW", "description": "View rentals"},
                {"id": "5", "code": "CUSTOMER_VIEW", "type": "CUSTOMER_VIEW", "description": "View customers"},
                {"id": "6", "code": "INVENTORY_VIEW", "type": "INVENTORY_VIEW", "description": "View inventory"},
                {"id": "7", "code": "REPORT_VIEW", "type": "REPORT_VIEW", "description": "View reports"},
            ]
        },
        "isActive": True,
        "createdAt": "2025-01-01T00:00:00Z"
    },
    "staff@example.com": {
        "id": "3",
        "email": "staff@example.com",
        "username": "staff",
        "firstName": "Staff",
        "lastName": "User",
        "name": "Staff User",
        "password": "staff123",
        "role": {
            "id": "3",
            "name": "Staff",
            "description": "Basic access",
            "permissions": [
                {"id": "1", "code": "SALE_CREATE", "type": "SALE_CREATE", "description": "Create sales"},
                {"id": "2", "code": "SALE_VIEW", "type": "SALE_VIEW", "description": "View sales"},
                {"id": "3", "code": "RENTAL_VIEW", "type": "RENTAL_VIEW", "description": "View rentals"},
                {"id": "4", "code": "CUSTOMER_VIEW", "type": "CUSTOMER_VIEW", "description": "View customers"},
                {"id": "5", "code": "INVENTORY_VIEW", "type": "INVENTORY_VIEW", "description": "View inventory"},
            ]
        },
        "isActive": True,
        "createdAt": "2025-01-01T00:00:00Z"
    }
}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    success: bool
    data: dict
    message: str


def create_simple_token(user_data: dict) -> str:
    """Create a simple token for demo purposes"""
    payload = {
        "sub": user_data["email"],
        "user_id": user_data["id"],
        "permissions": [p["code"] for p in user_data["role"]["permissions"]],
        "exp": (datetime.utcnow() + timedelta(hours=24)).timestamp()
    }
    # Simple base64 encoding (not secure, just for demo)
    token_str = json.dumps(payload)
    return base64.b64encode(token_str.encode()).decode()


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Demo login endpoint"""
    email = str(login_data.email).lower()
    
    if email not in DEMO_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user = DEMO_USERS[email]
    
    if user["password"] != login_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    access_token = create_simple_token(user)
    refresh_token = create_simple_token(user)  # Same for demo
    
    # Remove password from response
    user_response = {k: v for k, v in user.items() if k != "password"}
    
    return LoginResponse(
        success=True,
        data={
            "user": user_response,
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": 86400  # 24 hours
        },
        message="Login successful"
    )


@router.post("/refresh")
async def refresh_token():
    """Demo refresh endpoint"""
    return {"success": True, "message": "Token refreshed"}


@router.get("/me")
async def get_current_user():
    """Demo current user endpoint"""
    return {"success": True, "data": DEMO_USERS["admin@example.com"]}


@router.post("/logout")
async def logout():
    """Demo logout endpoint"""
    return {"success": True, "message": "Logged out successfully"}
