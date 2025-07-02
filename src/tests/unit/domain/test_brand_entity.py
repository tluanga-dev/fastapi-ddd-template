import pytest
from uuid import UUID, uuid4
from datetime import datetime

from src.domain.entities.brand import Brand


class TestBrandEntity:
    """Test Brand domain entity."""
    
    def test_create_brand_with_required_fields(self):
        """Test creating a brand with only required fields."""
        brand = Brand(
            brand_name="Nike"
        )
        
        assert brand.brand_name == "Nike"
        assert brand.brand_code is None
        assert brand.description is None
        assert brand.is_active is True
        assert isinstance(brand.id, UUID)
        assert isinstance(brand.created_at, datetime)
        assert isinstance(brand.updated_at, datetime)
    
    def test_create_brand_with_all_fields(self):
        """Test creating a brand with all fields."""
        brand = Brand(
            brand_name="Nike",
            brand_code="NIKE-001",
            description="Athletic footwear and apparel",
            created_by="admin",
            updated_by="admin"
        )
        
        assert brand.brand_name == "Nike"
        assert brand.brand_code == "NIKE-001"
        assert brand.description == "Athletic footwear and apparel"
        assert brand.created_by == "admin"
        assert brand.updated_by == "admin"
    
    def test_brand_name_validation_empty(self):
        """Test brand name cannot be empty."""
        with pytest.raises(ValueError, match="Brand name cannot be empty"):
            Brand(brand_name="")
    
    def test_brand_name_validation_whitespace(self):
        """Test brand name cannot be only whitespace."""
        with pytest.raises(ValueError, match="Brand name cannot be empty"):
            Brand(brand_name="   ")
    
    def test_brand_name_validation_length(self):
        """Test brand name length limit."""
        with pytest.raises(ValueError, match="Brand name cannot exceed 100 characters"):
            Brand(brand_name="A" * 101)
    
    def test_brand_code_validation_empty(self):
        """Test brand code cannot be empty if provided."""
        with pytest.raises(ValueError, match="Brand code cannot be empty if provided"):
            Brand(brand_name="Nike", brand_code="   ")
    
    def test_brand_code_validation_length(self):
        """Test brand code length limit."""
        with pytest.raises(ValueError, match="Brand code cannot exceed 20 characters"):
            Brand(brand_name="Nike", brand_code="A" * 21)
    
    def test_brand_code_validation_format(self):
        """Test brand code must be alphanumeric with hyphens/underscores."""
        # Valid codes
        valid_codes = ["NIKE001", "NIKE-001", "NIKE_001", "NK-2023_V1"]
        for code in valid_codes:
            brand = Brand(brand_name="Nike", brand_code=code)
            assert brand.brand_code == code
        
        # Invalid codes
        invalid_codes = ["NIKE@001", "NIKE#001", "NIKE 001", "NIKE.001"]
        for code in invalid_codes:
            with pytest.raises(ValueError, match="Brand code must contain only letters, numbers, hyphens, and underscores"):
                Brand(brand_name="Nike", brand_code=code)
    
    def test_description_validation_length(self):
        """Test description length limit."""
        with pytest.raises(ValueError, match="Brand description cannot exceed 500 characters"):
            Brand(brand_name="Nike", description="A" * 501)
    
    def test_update_name(self):
        """Test updating brand name."""
        brand = Brand(brand_name="Nike")
        
        brand.update_name("Nike Inc.", updated_by="admin")
        
        assert brand.brand_name == "Nike Inc."
        assert brand.updated_by == "admin"
        assert isinstance(brand.updated_at, datetime)
    
    def test_update_name_validation(self):
        """Test updating with invalid name fails."""
        brand = Brand(brand_name="Nike")
        
        with pytest.raises(ValueError, match="Brand name cannot be empty"):
            brand.update_name("")
        
        with pytest.raises(ValueError, match="Brand name cannot exceed 100 characters"):
            brand.update_name("A" * 101)
    
    def test_update_code(self):
        """Test updating brand code."""
        brand = Brand(brand_name="Nike", brand_code="NIKE-001")
        
        brand.update_code("NIKE-002", updated_by="admin")
        
        assert brand.brand_code == "NIKE-002"
        assert brand.updated_by == "admin"
    
    def test_update_code_to_none(self):
        """Test clearing brand code."""
        brand = Brand(brand_name="Nike", brand_code="NIKE-001")
        
        brand.update_code(None, updated_by="admin")
        
        assert brand.brand_code is None
        assert brand.updated_by == "admin"
    
    def test_update_code_validation(self):
        """Test updating with invalid code fails."""
        brand = Brand(brand_name="Nike", brand_code="NIKE-001")
        
        with pytest.raises(ValueError, match="Brand code cannot be empty if provided"):
            brand.update_code("   ")
        
        with pytest.raises(ValueError, match="Brand code cannot exceed 20 characters"):
            brand.update_code("A" * 21)
        
        with pytest.raises(ValueError, match="Brand code must contain only letters, numbers, hyphens, and underscores"):
            brand.update_code("NIKE@002")
    
    def test_update_description(self):
        """Test updating brand description."""
        brand = Brand(brand_name="Nike")
        
        brand.update_description("Leading athletic brand", updated_by="admin")
        
        assert brand.description == "Leading athletic brand"
        assert brand.updated_by == "admin"
    
    def test_update_description_to_none(self):
        """Test clearing brand description."""
        brand = Brand(brand_name="Nike", description="Old description")
        
        brand.update_description(None, updated_by="admin")
        
        assert brand.description is None
        assert brand.updated_by == "admin"
    
    def test_update_description_validation(self):
        """Test updating with invalid description fails."""
        brand = Brand(brand_name="Nike")
        
        with pytest.raises(ValueError, match="Brand description cannot exceed 500 characters"):
            brand.update_description("A" * 501)
    
    def test_deactivate(self):
        """Test deactivating a brand."""
        brand = Brand(brand_name="Nike")
        assert brand.is_active is True
        
        brand.deactivate(updated_by="admin")
        
        assert brand.is_active is False
        assert brand.updated_by == "admin"
        assert isinstance(brand.updated_at, datetime)
    
    def test_activate(self):
        """Test activating a brand."""
        brand = Brand(brand_name="Nike", is_active=False)
        assert brand.is_active is False
        
        brand.activate(updated_by="admin")
        
        assert brand.is_active is True
        assert brand.updated_by == "admin"
        assert isinstance(brand.updated_at, datetime)
    
    def test_string_representation(self):
        """Test string representation of brand."""
        brand = Brand(brand_name="Nike")
        assert str(brand) == "Brand(Nike)"
    
    def test_repr_representation(self):
        """Test developer representation of brand."""
        brand = Brand(
            brand_name="Nike",
            brand_code="NIKE-001",
            is_active=True
        )
        
        repr_str = repr(brand)
        assert "Nike" in repr_str
        assert "NIKE-001" in repr_str
        assert "is_active=True" in repr_str
        assert f"id={brand.id}" in repr_str
    
    def test_brand_inherits_base_entity(self):
        """Test that Brand properly inherits from BaseEntity."""
        brand = Brand(
            brand_name="Nike",
            created_by="creator",
            updated_by="updater"
        )
        
        assert isinstance(brand.id, UUID)
        assert isinstance(brand.created_at, datetime)
        assert isinstance(brand.updated_at, datetime)
        assert brand.created_by == "creator"
        assert brand.updated_by == "updater"
        assert brand.is_active is True
    
    def test_multiple_brands_unique_ids(self):
        """Test that multiple brands have unique IDs."""
        brand1 = Brand(brand_name="Nike")
        brand2 = Brand(brand_name="Adidas")
        brand3 = Brand(brand_name="Puma")
        
        assert brand1.id != brand2.id
        assert brand2.id != brand3.id
        assert brand1.id != brand3.id