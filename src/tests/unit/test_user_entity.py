import pytest
from datetime import datetime
from uuid import uuid4

from src.domain.entities.user import User
from src.domain.value_objects.email import Email


class TestUserEntity:
    def test_create_user(self):
        email = Email("test@example.com")
        user = User(
            email=email,
            name="Test User",
            hashed_password="hashed_password",
            is_superuser=False,
        )
        
        assert user.email == email
        assert user.name == "Test User"
        assert user.hashed_password == "hashed_password"
        assert user.is_superuser is False
        assert user.is_active is True
        assert isinstance(user.id, type(uuid4()))
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_update_email(self):
        user = User(
            email=Email("old@example.com"),
            name="Test User",
            hashed_password="hashed_password",
        )
        old_updated_at = user.updated_at
        
        new_email = Email("new@example.com")
        user.update_email(new_email, "admin")
        
        assert user.email == new_email
        assert user.updated_by == "admin"
        assert user.updated_at > old_updated_at

    def test_soft_delete(self):
        user = User(
            email=Email("test@example.com"),
            name="Test User",
            hashed_password="hashed_password",
        )
        
        assert user.is_active is True
        
        user.soft_delete("admin")
        
        assert user.is_active is False
        assert user.updated_by == "admin"

    def test_make_superuser(self):
        user = User(
            email=Email("test@example.com"),
            name="Test User",
            hashed_password="hashed_password",
            is_superuser=False,
        )
        
        assert user.is_superuser is False
        
        user.make_superuser("admin")
        
        assert user.is_superuser is True
        assert user.updated_by == "admin"


class TestEmailValueObject:
    def test_valid_email(self):
        email = Email("test@example.com")
        assert email.value == "test@example.com"

    def test_email_lowercase(self):
        email = Email("Test@Example.COM")
        assert email.value == "test@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("invalid-email")
        
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("@example.com")
        
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("test@")

    def test_email_equality(self):
        email1 = Email("test@example.com")
        email2 = Email("test@example.com")
        email3 = Email("other@example.com")
        
        assert email1 == email2
        assert email1 != email3
        assert email1 != "test@example.com"