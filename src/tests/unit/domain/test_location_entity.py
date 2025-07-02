import pytest
from uuid import UUID, uuid4
from datetime import datetime

from src.domain.entities.location import Location, LocationType
from src.domain.value_objects.phone_number import PhoneNumber


class TestLocationEntity:
    """Test Location domain entity."""
    
    def test_create_valid_location(self):
        """Test creating a valid location."""
        location = Location(
            location_code="LOC001",
            location_name="Main Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            contact_number="+12125551234",
            email="mainstore@example.com",
            manager_user_id=uuid4()
        )
        
        assert location.location_code == "LOC001"
        assert location.location_name == "Main Store"
        assert location.location_type == LocationType.STORE
        assert location.address == "123 Main St"
        assert location.city == "New York"
        assert location.state == "NY"
        assert location.country == "USA"
        assert location.postal_code == "10001"
        assert location.contact_number == "+12125551234"
        assert location.email == "mainstore@example.com"
        assert isinstance(location.manager_user_id, UUID)
        assert location.is_active is True
    
    def test_create_location_minimal(self):
        """Test creating location with minimal required fields."""
        location = Location(
            location_code="LOC002",
            location_name="Warehouse A",
            location_type=LocationType.WAREHOUSE,
            address="456 Storage Rd",
            city="Los Angeles",
            state="CA",
            country="USA"
        )
        
        assert location.location_code == "LOC002"
        assert location.postal_code is None
        assert location.contact_number is None
        assert location.email is None
        assert location.manager_user_id is None
    
    def test_location_type_validation(self):
        """Test location type must be valid enum value."""
        with pytest.raises(ValueError, match="Invalid location type"):
            Location(
                location_code="LOC003",
                location_name="Invalid Type",
                location_type="INVALID",
                address="789 Test St",
                city="Chicago",
                state="IL",
                country="USA"
            )
    
    def test_location_code_validation(self):
        """Test location code cannot be empty."""
        with pytest.raises(ValueError, match="Location code cannot be empty"):
            Location(
                location_code="",
                location_name="No Code Store",
                location_type=LocationType.STORE,
                address="123 Test St",
                city="Miami",
                state="FL",
                country="USA"
            )
    
    def test_location_name_validation(self):
        """Test location name cannot be empty."""
        with pytest.raises(ValueError, match="Location name cannot be empty"):
            Location(
                location_code="LOC004",
                location_name="",
                location_type=LocationType.STORE,
                address="123 Test St",
                city="Miami",
                state="FL",
                country="USA"
            )
    
    def test_address_validation(self):
        """Test address cannot be empty."""
        with pytest.raises(ValueError, match="Address cannot be empty"):
            Location(
                location_code="LOC005",
                location_name="No Address Store",
                location_type=LocationType.STORE,
                address="",
                city="Miami",
                state="FL",
                country="USA"
            )
    
    def test_city_validation(self):
        """Test city cannot be empty."""
        with pytest.raises(ValueError, match="City cannot be empty"):
            Location(
                location_code="LOC006",
                location_name="No City Store",
                location_type=LocationType.STORE,
                address="123 Test St",
                city="",
                state="FL",
                country="USA"
            )
    
    def test_email_validation(self):
        """Test email format validation."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Location(
                location_code="LOC007",
                location_name="Bad Email Store",
                location_type=LocationType.STORE,
                address="123 Test St",
                city="Miami",
                state="FL",
                country="USA",
                email="notanemail"
            )
    
    def test_phone_number_validation(self):
        """Test phone number validation."""
        with pytest.raises(ValueError, match="Invalid contact number"):
            Location(
                location_code="LOC008",
                location_name="Bad Phone Store",
                location_type=LocationType.STORE,
                address="123 Test St",
                city="Miami",
                state="FL",
                country="USA",
                contact_number="123ABC"
            )
    
    def test_update_details(self):
        """Test updating location details."""
        location = Location(
            location_code="LOC009",
            location_name="Original Store",
            location_type=LocationType.STORE,
            address="123 Old St",
            city="Old City",
            state="OC",
            country="USA"
        )
        
        location.update_details(
            location_name="Updated Store",
            address="456 New St",
            city="New City",
            state="NC",
            country="Canada",
            postal_code="12345",
            updated_by="user123"
        )
        
        assert location.location_name == "Updated Store"
        assert location.address == "456 New St"
        assert location.city == "New City"
        assert location.state == "NC"
        assert location.country == "Canada"
        assert location.postal_code == "12345"
        assert location.updated_by == "user123"
        assert isinstance(location.updated_at, datetime)
    
    def test_update_contact_info(self):
        """Test updating contact information."""
        location = Location(
            location_code="LOC010",
            location_name="Contact Test Store",
            location_type=LocationType.STORE,
            address="123 Test St",
            city="Test City",
            state="TC",
            country="USA"
        )
        
        location.update_contact_info(
            contact_number="+19175551234",
            email="newcontact@example.com",
            updated_by="user456"
        )
        
        assert location.contact_number == "+19175551234"
        assert location.email == "newcontact@example.com"
        assert location.updated_by == "user456"
    
    def test_clear_contact_info(self):
        """Test clearing contact information."""
        location = Location(
            location_code="LOC011",
            location_name="Clear Contact Store",
            location_type=LocationType.STORE,
            address="123 Test St",
            city="Test City",
            state="TC",
            country="USA",
            contact_number="+12125551234",
            email="store@example.com"
        )
        
        location.update_contact_info(
            contact_number=None,
            email=None
        )
        
        assert location.contact_number is None
        assert location.email is None
    
    def test_assign_manager(self):
        """Test assigning a manager to location."""
        location = Location(
            location_code="LOC012",
            location_name="Manager Test Store",
            location_type=LocationType.STORE,
            address="123 Test St",
            city="Test City",
            state="TC",
            country="USA"
        )
        
        manager_id = uuid4()
        location.assign_manager(manager_id, updated_by="admin")
        
        assert location.manager_user_id == manager_id
        assert location.updated_by == "admin"
    
    def test_remove_manager(self):
        """Test removing manager from location."""
        manager_id = uuid4()
        location = Location(
            location_code="LOC013",
            location_name="Remove Manager Store",
            location_type=LocationType.STORE,
            address="123 Test St",
            city="Test City",
            state="TC",
            country="USA",
            manager_user_id=manager_id
        )
        
        location.remove_manager(updated_by="admin")
        
        assert location.manager_user_id is None
        assert location.updated_by == "admin"
    
    def test_deactivate_location(self):
        """Test deactivating a location."""
        location = Location(
            location_code="LOC014",
            location_name="Active Store",
            location_type=LocationType.STORE,
            address="123 Test St",
            city="Test City",
            state="TC",
            country="USA"
        )
        
        assert location.is_active is True
        
        location.deactivate(updated_by="admin")
        
        assert location.is_active is False
        assert location.updated_by == "admin"
    
    def test_activate_location(self):
        """Test activating a location."""
        location = Location(
            location_code="LOC015",
            location_name="Inactive Store",
            location_type=LocationType.STORE,
            address="123 Test St",
            city="Test City",
            state="TC",
            country="USA",
            is_active=False
        )
        
        assert location.is_active is False
        
        location.activate(updated_by="admin")
        
        assert location.is_active is True
        assert location.updated_by == "admin"
    
    def test_get_full_address(self):
        """Test getting full formatted address."""
        location = Location(
            location_code="LOC016",
            location_name="Address Test Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001"
        )
        
        expected = "123 Main St, New York, NY, 10001, USA"
        assert location.get_full_address() == expected
    
    def test_get_full_address_without_postal(self):
        """Test getting full address without postal code."""
        location = Location(
            location_code="LOC017",
            location_name="No Postal Store",
            location_type=LocationType.STORE,
            address="456 Broadway",
            city="Los Angeles",
            state="CA",
            country="USA"
        )
        
        expected = "456 Broadway, Los Angeles, CA, USA"
        assert location.get_full_address() == expected
    
    def test_location_type_checks(self):
        """Test location type checking methods."""
        store = Location(
            location_code="LOC018",
            location_name="Store",
            location_type=LocationType.STORE,
            address="123 Store St",
            city="City",
            state="ST",
            country="USA"
        )
        
        warehouse = Location(
            location_code="LOC019",
            location_name="Warehouse",
            location_type=LocationType.WAREHOUSE,
            address="456 Warehouse Rd",
            city="City",
            state="ST",
            country="USA"
        )
        
        service_center = Location(
            location_code="LOC020",
            location_name="Service Center",
            location_type=LocationType.SERVICE_CENTER,
            address="789 Service Ave",
            city="City",
            state="ST",
            country="USA"
        )
        
        assert store.is_store() is True
        assert store.is_warehouse() is False
        assert store.is_service_center() is False
        
        assert warehouse.is_store() is False
        assert warehouse.is_warehouse() is True
        assert warehouse.is_service_center() is False
        
        assert service_center.is_store() is False
        assert service_center.is_warehouse() is False
        assert service_center.is_service_center() is True
    
    def test_location_inherits_base_entity(self):
        """Test that Location properly inherits from BaseEntity."""
        location = Location(
            location_code="LOC021",
            location_name="Base Test Store",
            location_type=LocationType.STORE,
            address="123 Test St",
            city="Test City",
            state="TC",
            country="USA",
            created_by="creator",
            updated_by="updater"
        )
        
        assert isinstance(location.id, UUID)
        assert isinstance(location.created_at, datetime)
        assert isinstance(location.updated_at, datetime)
        assert location.created_by == "creator"
        assert location.updated_by == "updater"
        assert location.is_active is True