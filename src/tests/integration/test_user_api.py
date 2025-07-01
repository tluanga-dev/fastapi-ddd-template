import pytest
from httpx import AsyncClient
from fastapi import status

from src.main import app


@pytest.mark.asyncio
@pytest.mark.integration
class TestUserAPI:
    async def test_create_user(self, override_get_db):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/users/",
                json={
                    "email": "test@example.com",
                    "name": "Test User",
                    "password": "testpassword123",
                    "is_superuser": False,
                },
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["name"] == "Test User"
            assert data["is_superuser"] is False
            assert data["is_active"] is True
            assert "id" in data
            assert "created_at" in data
            assert "updated_at" in data

    async def test_create_duplicate_user(self, override_get_db):
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create first user
            await client.post(
                "/api/v1/users/",
                json={
                    "email": "test@example.com",
                    "name": "Test User",
                    "password": "testpassword123",
                    "is_superuser": False,
                },
            )
            
            # Try to create duplicate
            response = await client.post(
                "/api/v1/users/",
                json={
                    "email": "test@example.com",
                    "name": "Another User",
                    "password": "anotherpassword123",
                    "is_superuser": False,
                },
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "already exists" in response.json()["detail"]

    async def test_get_user(self, override_get_db):
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create user
            create_response = await client.post(
                "/api/v1/users/",
                json={
                    "email": "test@example.com",
                    "name": "Test User",
                    "password": "testpassword123",
                    "is_superuser": False,
                },
            )
            user_id = create_response.json()["id"]
            
            # Get user
            response = await client.get(f"/api/v1/users/{user_id}")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == user_id
            assert data["email"] == "test@example.com"
            assert data["name"] == "Test User"

    async def test_get_nonexistent_user(self, override_get_db):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"]

    async def test_list_users(self, override_get_db):
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create multiple users
            for i in range(3):
                await client.post(
                    "/api/v1/users/",
                    json={
                        "email": f"test{i}@example.com",
                        "name": f"Test User {i}",
                        "password": "testpassword123",
                        "is_superuser": False,
                    },
                )
            
            # List users
            response = await client.get("/api/v1/users/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 3
            assert all(user["is_active"] for user in data)

    async def test_update_user(self, override_get_db):
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create user
            create_response = await client.post(
                "/api/v1/users/",
                json={
                    "email": "test@example.com",
                    "name": "Test User",
                    "password": "testpassword123",
                    "is_superuser": False,
                },
            )
            user_id = create_response.json()["id"]
            
            # Update user
            response = await client.patch(
                f"/api/v1/users/{user_id}",
                json={
                    "name": "Updated User",
                    "email": "updated@example.com",
                },
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "Updated User"
            assert data["email"] == "updated@example.com"

    async def test_delete_user(self, override_get_db):
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create user
            create_response = await client.post(
                "/api/v1/users/",
                json={
                    "email": "test@example.com",
                    "name": "Test User",
                    "password": "testpassword123",
                    "is_superuser": False,
                },
            )
            user_id = create_response.json()["id"]
            
            # Delete user
            response = await client.delete(f"/api/v1/users/{user_id}")
            
            assert response.status_code == status.HTTP_204_NO_CONTENT
            
            # Verify user is soft deleted (inactive)
            get_response = await client.get(f"/api/v1/users/{user_id}")
            assert get_response.json()["is_active"] is False