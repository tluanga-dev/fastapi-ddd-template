import pytest
from uuid import UUID, uuid4
from datetime import datetime

from src.domain.entities.category import Category, CategoryPath


class TestCategoryEntity:
    """Test Category domain entity."""
    
    def test_create_root_category(self):
        """Test creating a root category."""
        category = Category(
            category_name="Electronics",
            parent_category_id=None,
            category_path="Electronics",
            category_level=1,
            display_order=0,
            is_leaf=True
        )
        
        assert category.category_name == "Electronics"
        assert category.parent_category_id is None
        assert category.category_path == "Electronics"
        assert category.category_level == 1
        assert category.display_order == 0
        assert category.is_leaf is True
        assert category.is_active is True
    
    def test_create_child_category(self):
        """Test creating a child category."""
        parent_id = uuid4()
        category = Category(
            category_name="Laptops",
            parent_category_id=parent_id,
            category_path="Electronics/Computers/Laptops",
            category_level=3,
            display_order=2,
            is_leaf=True
        )
        
        assert category.category_name == "Laptops"
        assert category.parent_category_id == parent_id
        assert category.category_path == "Electronics/Computers/Laptops"
        assert category.category_level == 3
        assert category.display_order == 2
    
    def test_category_name_validation(self):
        """Test category name cannot be empty."""
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            Category(
                category_name="",
                parent_category_id=None,
                category_path="",
                category_level=1
            )
    
    def test_category_name_whitespace_validation(self):
        """Test category name cannot be only whitespace."""
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            Category(
                category_name="   ",
                parent_category_id=None,
                category_path="Electronics",
                category_level=1
            )
    
    def test_category_name_length_validation(self):
        """Test category name length limit."""
        with pytest.raises(ValueError, match="Category name cannot exceed 100 characters"):
            Category(
                category_name="A" * 101,
                parent_category_id=None,
                category_path="A" * 101,
                category_level=1
            )
    
    def test_category_level_validation(self):
        """Test category level must be at least 1."""
        with pytest.raises(ValueError, match="Category level must be at least 1"):
            Category(
                category_name="Invalid",
                parent_category_id=None,
                category_path="Invalid",
                category_level=0
            )
    
    def test_display_order_validation(self):
        """Test display order cannot be negative."""
        with pytest.raises(ValueError, match="Display order cannot be negative"):
            Category(
                category_name="Electronics",
                parent_category_id=None,
                category_path="Electronics",
                category_level=1,
                display_order=-1
            )
    
    def test_root_category_without_parent(self):
        """Test root category cannot have parent."""
        with pytest.raises(ValueError, match="Root categories cannot have a parent"):
            Category(
                category_name="Electronics",
                parent_category_id=uuid4(),
                category_path="Electronics",
                category_level=1
            )
    
    def test_non_root_category_with_parent(self):
        """Test non-root category must have parent."""
        with pytest.raises(ValueError, match="Non-root categories must have a parent"):
            Category(
                category_name="Computers",
                parent_category_id=None,
                category_path="Electronics/Computers",
                category_level=2
            )
    
    def test_update_name(self):
        """Test updating category name."""
        category = Category(
            category_name="Electronic",  # Typo
            parent_category_id=None,
            category_path="Electronic",
            category_level=1
        )
        
        category.update_name("Electronics", updated_by="admin")
        
        assert category.category_name == "Electronics"
        assert category.updated_by == "admin"
        assert isinstance(category.updated_at, datetime)
    
    def test_update_name_empty_validation(self):
        """Test updating with empty name fails."""
        category = Category(
            category_name="Electronics",
            parent_category_id=None,
            category_path="Electronics",
            category_level=1
        )
        
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            category.update_name("")
    
    def test_update_display_order(self):
        """Test updating display order."""
        category = Category(
            category_name="Electronics",
            parent_category_id=None,
            category_path="Electronics",
            category_level=1,
            display_order=0
        )
        
        category.update_display_order(5, updated_by="admin")
        
        assert category.display_order == 5
        assert category.updated_by == "admin"
    
    def test_update_display_order_negative_validation(self):
        """Test updating with negative display order fails."""
        category = Category(
            category_name="Electronics",
            parent_category_id=None,
            category_path="Electronics",
            category_level=1
        )
        
        with pytest.raises(ValueError, match="Display order cannot be negative"):
            category.update_display_order(-1)
    
    def test_mark_as_parent(self):
        """Test marking category as parent (not leaf)."""
        category = Category(
            category_name="Electronics",
            parent_category_id=None,
            category_path="Electronics",
            category_level=1,
            is_leaf=True
        )
        
        assert category.is_leaf is True
        
        category.mark_as_parent(updated_by="system")
        
        assert category.is_leaf is False
        assert category.updated_by == "system"
    
    def test_mark_as_leaf(self):
        """Test marking category as leaf."""
        category = Category(
            category_name="Electronics",
            parent_category_id=None,
            category_path="Electronics",
            category_level=1,
            is_leaf=False
        )
        
        assert category.is_leaf is False
        
        category.mark_as_leaf(updated_by="system")
        
        assert category.is_leaf is True
        assert category.updated_by == "system"
    
    def test_update_path(self):
        """Test updating category path."""
        parent_id = uuid4()
        category = Category(
            category_name="Laptops",
            parent_category_id=parent_id,
            category_path="Electronic/Computers/Laptops",  # Typo in parent
            category_level=3
        )
        
        category.update_path("Electronics/Computers/Laptops", updated_by="system")
        
        assert category.category_path == "Electronics/Computers/Laptops"
        assert category.updated_by == "system"
    
    def test_update_path_empty_validation(self):
        """Test updating with empty path fails."""
        category = Category(
            category_name="Electronics",
            parent_category_id=None,
            category_path="Electronics",
            category_level=1
        )
        
        with pytest.raises(ValueError, match="Category path cannot be empty"):
            category.update_path("")
    
    def test_can_have_products(self):
        """Test checking if category can have products."""
        leaf_category = Category(
            category_name="Laptops",
            parent_category_id=uuid4(),
            category_path="Electronics/Computers/Laptops",
            category_level=3,
            is_leaf=True
        )
        
        parent_category = Category(
            category_name="Computers",
            parent_category_id=uuid4(),
            category_path="Electronics/Computers",
            category_level=2,
            is_leaf=False
        )
        
        assert leaf_category.can_have_products() is True
        assert parent_category.can_have_products() is False
    
    def test_is_root(self):
        """Test checking if category is root."""
        root_category = Category(
            category_name="Electronics",
            parent_category_id=None,
            category_path="Electronics",
            category_level=1
        )
        
        child_category = Category(
            category_name="Computers",
            parent_category_id=uuid4(),
            category_path="Electronics/Computers",
            category_level=2
        )
        
        assert root_category.is_root() is True
        assert child_category.is_root() is False
    
    def test_get_path_segments(self):
        """Test getting path segments."""
        category = Category(
            category_name="Laptops",
            parent_category_id=uuid4(),
            category_path="Electronics/Computers/Laptops",
            category_level=3
        )
        
        segments = category.get_path_segments()
        
        assert segments == ["Electronics", "Computers", "Laptops"]
        assert len(segments) == 3
    
    def test_get_depth(self):
        """Test getting category depth."""
        categories = [
            Category(
                category_name="Electronics",
                parent_category_id=None,
                category_path="Electronics",
                category_level=1
            ),
            Category(
                category_name="Computers",
                parent_category_id=uuid4(),
                category_path="Electronics/Computers",
                category_level=2
            ),
            Category(
                category_name="Laptops",
                parent_category_id=uuid4(),
                category_path="Electronics/Computers/Laptops",
                category_level=3
            )
        ]
        
        assert categories[0].get_depth() == 1
        assert categories[1].get_depth() == 2
        assert categories[2].get_depth() == 3
    
    def test_string_representation(self):
        """Test string representation of category."""
        category = Category(
            category_name="Laptops",
            parent_category_id=uuid4(),
            category_path="Electronics/Computers/Laptops",
            category_level=3
        )
        
        assert str(category) == "Category(Electronics/Computers/Laptops)"
    
    def test_repr_representation(self):
        """Test developer representation of category."""
        category = Category(
            category_name="Laptops",
            parent_category_id=uuid4(),
            category_path="Electronics/Computers/Laptops",
            category_level=3,
            is_leaf=True
        )
        
        repr_str = repr(category)
        assert "Laptops" in repr_str
        assert "Electronics/Computers/Laptops" in repr_str
        assert "level=3" in repr_str
        assert "is_leaf=True" in repr_str
    
    def test_category_inherits_base_entity(self):
        """Test that Category properly inherits from BaseEntity."""
        category = Category(
            category_name="Electronics",
            parent_category_id=None,
            category_path="Electronics",
            category_level=1,
            created_by="creator",
            updated_by="updater"
        )
        
        assert isinstance(category.id, UUID)
        assert isinstance(category.created_at, datetime)
        assert isinstance(category.updated_at, datetime)
        assert category.created_by == "creator"
        assert category.updated_by == "updater"
        assert category.is_active is True


class TestCategoryPath:
    """Test CategoryPath value object."""
    
    def test_create_category_path(self):
        """Test creating a category path."""
        path = CategoryPath("Electronics/Computers/Laptops")
        assert str(path) == "Electronics/Computers/Laptops"
    
    def test_create_path_strips_slashes(self):
        """Test path strips leading/trailing slashes."""
        path = CategoryPath("/Electronics/Computers/")
        assert str(path) == "Electronics/Computers"
    
    def test_empty_path_validation(self):
        """Test empty path is invalid."""
        with pytest.raises(ValueError, match="Category path cannot be empty"):
            CategoryPath("")
    
    def test_append_segment(self):
        """Test appending segment to path."""
        path = CategoryPath("Electronics/Computers")
        new_path = path.append("Laptops")
        
        assert str(new_path) == "Electronics/Computers/Laptops"
        assert str(path) == "Electronics/Computers"  # Original unchanged
    
    def test_append_empty_segment_fails(self):
        """Test appending empty segment fails."""
        path = CategoryPath("Electronics")
        
        with pytest.raises(ValueError, match="Path segment cannot be empty"):
            path.append("")
    
    def test_parent_path(self):
        """Test getting parent path."""
        path = CategoryPath("Electronics/Computers/Laptops")
        parent = path.parent_path()
        
        assert str(parent) == "Electronics/Computers"
        
        grandparent = parent.parent_path()
        assert str(grandparent) == "Electronics"
        
        root_parent = grandparent.parent_path()
        assert root_parent is None
    
    def test_replace_segment(self):
        """Test replacing segment in path."""
        path = CategoryPath("Electronic/Computers/Laptops")  # Typo
        new_path = path.replace_segment("Electronic", "Electronics")
        
        assert str(new_path) == "Electronics/Computers/Laptops"
    
    def test_starts_with(self):
        """Test checking if path starts with prefix."""
        path = CategoryPath("Electronics/Computers/Laptops")
        
        assert path.starts_with("Electronics") is True
        assert path.starts_with("Electronics/Computers") is True
        assert path.starts_with("Computers") is False
    
    def test_get_segments(self):
        """Test getting path segments."""
        path = CategoryPath("Electronics/Computers/Laptops")
        segments = path.get_segments()
        
        assert segments == ["Electronics", "Computers", "Laptops"]
    
    def test_get_level(self):
        """Test getting path level."""
        paths = [
            CategoryPath("Electronics"),
            CategoryPath("Electronics/Computers"),
            CategoryPath("Electronics/Computers/Laptops")
        ]
        
        assert paths[0].get_level() == 1
        assert paths[1].get_level() == 2
        assert paths[2].get_level() == 3
    
    def test_equality(self):
        """Test path equality."""
        path1 = CategoryPath("Electronics/Computers")
        path2 = CategoryPath("Electronics/Computers")
        path3 = CategoryPath("Electronics/Laptops")
        
        assert path1 == path2
        assert path1 != path3
        assert path1 != "Electronics/Computers"  # Not same type