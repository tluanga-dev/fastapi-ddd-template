import pytest
from uuid import UUID, uuid4
from datetime import datetime

from src.domain.entities.customer_contact_method import CustomerContactMethod
from src.domain.value_objects.customer_type import ContactType


class TestCustomerContactMethodEntity:
    """Test CustomerContactMethod domain entity."""
    
    def test_create_email_contact(self):
        """Test creating an email contact method."""
        customer_id = uuid4()
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="john.doe@example.com",
            contact_label="Personal",
            is_primary=True,
            opt_in_marketing=True
        )
        
        assert contact.customer_id == customer_id
        assert contact.contact_type == ContactType.EMAIL
        assert contact.contact_value == "john.doe@example.com"
        assert contact.contact_label == "Personal"
        assert contact.is_primary is True
        assert contact.is_verified is False
        assert contact.verified_date is None
        assert contact.opt_in_marketing is True
        assert contact.is_active is True
        assert isinstance(contact.id, UUID)
    
    def test_create_phone_contact(self):
        """Test creating a phone contact method."""
        customer_id = uuid4()
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.MOBILE,
            contact_value="+1234567890",
            contact_label="Work",
            is_primary=False
        )
        
        assert contact.customer_id == customer_id
        assert contact.contact_type == ContactType.MOBILE
        assert contact.contact_value == "+1234567890"
        assert contact.contact_label == "Work"
        assert contact.is_primary is False
    
    def test_customer_id_required(self):
        """Test customer ID is required."""
        with pytest.raises(ValueError, match="Customer ID is required"):
            CustomerContactMethod(
                customer_id=None,
                contact_type=ContactType.EMAIL,
                contact_value="test@example.com"
            )
    
    def test_contact_value_validation(self):
        """Test contact value validation."""
        customer_id = uuid4()
        
        # Empty value
        with pytest.raises(ValueError, match="Contact value cannot be empty"):
            CustomerContactMethod(
                customer_id=customer_id,
                contact_type=ContactType.EMAIL,
                contact_value=""
            )
        
        # Whitespace only
        with pytest.raises(ValueError, match="Contact value cannot be empty"):
            CustomerContactMethod(
                customer_id=customer_id,
                contact_type=ContactType.EMAIL,
                contact_value="   "
            )
        
        # Too long
        with pytest.raises(ValueError, match="Contact value cannot exceed 100 characters"):
            CustomerContactMethod(
                customer_id=customer_id,
                contact_type=ContactType.EMAIL,
                contact_value="a" * 101
            )
    
    def test_contact_label_validation(self):
        """Test contact label validation."""
        customer_id = uuid4()
        
        # Too long label
        with pytest.raises(ValueError, match="Contact label cannot exceed 50 characters"):
            CustomerContactMethod(
                customer_id=customer_id,
                contact_type=ContactType.EMAIL,
                contact_value="test@example.com",
                contact_label="A" * 51
            )
    
    def test_email_format_validation(self):
        """Test email format validation."""
        customer_id = uuid4()
        
        # Invalid email format
        with pytest.raises(ValueError, match="Invalid email format"):
            CustomerContactMethod(
                customer_id=customer_id,
                contact_type=ContactType.EMAIL,
                contact_value="invalid-email"
            )
        
        # Valid email
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com"
        )
        assert contact.contact_value == "test@example.com"
    
    def test_phone_format_validation(self):
        """Test phone number format validation."""
        customer_id = uuid4()
        
        # Invalid phone format - letters in phone number
        with pytest.raises(ValueError, match="Invalid phone number format"):
            CustomerContactMethod(
                customer_id=customer_id,
                contact_type=ContactType.MOBILE,
                contact_value="123-CALL"
            )
        
        # Valid phone
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.MOBILE,
            contact_value="+1234567890"
        )
        assert contact.contact_value == "+1234567890"
    
    def test_verified_date_consistency(self):
        """Test verified date consistency."""
        customer_id = uuid4()
        
        # Cannot have verified date if not verified
        with pytest.raises(ValueError, match="Verified date cannot be set when contact is not verified"):
            CustomerContactMethod(
                customer_id=customer_id,
                contact_type=ContactType.EMAIL,
                contact_value="test@example.com",
                is_verified=False,
                verified_date=datetime.utcnow()
            )
        
        # Auto-set verified date if verified
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com",
            is_verified=True
        )
        assert contact.verified_date is not None
        assert isinstance(contact.verified_date, datetime)
    
    def test_get_formatted_value(self):
        """Test getting formatted contact value."""
        customer_id = uuid4()
        
        # Email
        email_contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="TEST@EXAMPLE.COM"
        )
        assert email_contact.get_formatted_value() == "test@example.com"  # Lowercase
        
        # Phone
        phone_contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.MOBILE,
            contact_value="+1234567890"
        )
        assert phone_contact.get_formatted_value() == "+1234567890"
        
        # Fax (no special formatting)
        fax_contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.FAX,
            contact_value="123-456-7890"
        )
        assert fax_contact.get_formatted_value() == "123-456-7890"
    
    def test_set_as_primary(self):
        """Test setting contact as primary."""
        customer_id = uuid4()
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com",
            is_primary=False
        )
        
        assert contact.is_primary is False
        
        contact.set_as_primary(updated_by="admin")
        
        assert contact.is_primary is True
        assert contact.updated_by == "admin"
        assert isinstance(contact.updated_at, datetime)
    
    def test_remove_as_primary(self):
        """Test removing primary status."""
        customer_id = uuid4()
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com",
            is_primary=True
        )
        
        contact.remove_as_primary(updated_by="admin")
        
        assert contact.is_primary is False
        assert contact.updated_by == "admin"
    
    def test_verify(self):
        """Test verifying contact."""
        customer_id = uuid4()
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com",
            is_verified=False
        )
        
        assert contact.is_verified is False
        assert contact.verified_date is None
        
        contact.verify(updated_by="system")
        
        assert contact.is_verified is True
        assert contact.verified_date is not None
        assert isinstance(contact.verified_date, datetime)
        assert contact.updated_by == "system"
    
    def test_verify_already_verified_fails(self):
        """Test verifying already verified contact fails."""
        customer_id = uuid4()
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com",
            is_verified=True
        )
        
        with pytest.raises(ValueError, match="Contact is already verified"):
            contact.verify()
    
    def test_unverify(self):
        """Test unverifying contact."""
        customer_id = uuid4()
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com",
            is_verified=True
        )
        
        contact.unverify(updated_by="admin")
        
        assert contact.is_verified is False
        assert contact.verified_date is None
        assert contact.updated_by == "admin"
    
    def test_unverify_not_verified_fails(self):
        """Test unverifying non-verified contact fails."""
        customer_id = uuid4()
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com",
            is_verified=False
        )
        
        with pytest.raises(ValueError, match="Contact is already unverified"):
            contact.unverify()
    
    def test_update_marketing_consent(self):
        """Test updating marketing consent."""
        customer_id = uuid4()
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com",
            opt_in_marketing=True
        )
        
        contact.update_marketing_consent(False, updated_by="customer")
        
        assert contact.opt_in_marketing is False
        assert contact.updated_by == "customer"
    
    def test_update_label(self):
        """Test updating contact label."""
        customer_id = uuid4()
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com",
            contact_label="Personal"
        )
        
        contact.update_label("Work", updated_by="admin")
        
        assert contact.contact_label == "Work"
        assert contact.updated_by == "admin"
        
        # Update to None
        contact.update_label(None, updated_by="admin")
        assert contact.contact_label is None
    
    def test_update_label_too_long_fails(self):
        """Test updating label with too long value fails."""
        customer_id = uuid4()
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com"
        )
        
        with pytest.raises(ValueError, match="Contact label cannot exceed 50 characters"):
            contact.update_label("A" * 51)
    
    def test_is_email(self):
        """Test checking if contact is email."""
        customer_id = uuid4()
        
        email_contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com"
        )
        assert email_contact.is_email() is True
        assert email_contact.is_phone() is False
        
        phone_contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.MOBILE,
            contact_value="+1234567890"
        )
        assert phone_contact.is_email() is False
    
    def test_is_phone(self):
        """Test checking if contact is phone."""
        customer_id = uuid4()
        
        mobile_contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.MOBILE,
            contact_value="+1234567890"
        )
        assert mobile_contact.is_phone() is True
        
        phone_contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.PHONE,
            contact_value="+1234567890"
        )
        assert phone_contact.is_phone() is True
        
        email_contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com"
        )
        assert email_contact.is_phone() is False
    
    def test_string_representation(self):
        """Test string representation."""
        customer_id = uuid4()
        
        # With label and primary
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com",
            contact_label="Work",
            is_primary=True
        )
        assert str(contact) == "EMAIL: test@example.com (Work) [Primary]"
        
        # Without label, not primary
        contact2 = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.MOBILE,
            contact_value="+1234567890"
        )
        assert str(contact2) == "MOBILE: +1234567890"
    
    def test_repr_representation(self):
        """Test developer representation."""
        customer_id = uuid4()
        contact = CustomerContactMethod(
            customer_id=customer_id,
            contact_type=ContactType.EMAIL,
            contact_value="test@example.com",
            is_primary=True,
            is_verified=True
        )
        
        repr_str = repr(contact)
        assert "EMAIL" in repr_str
        assert "test@example.com" in repr_str
        assert "primary=True" in repr_str
        assert "verified=True" in repr_str
        assert f"id={contact.id}" in repr_str