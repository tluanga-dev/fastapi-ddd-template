from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.role import Role, Permission
from src.domain.repositories.role_repository import RoleRepository
from src.infrastructure.models.auth_models import RoleModel, PermissionModel, role_permission_association
from src.infrastructure.repositories.base import SQLAlchemyRepository


class RoleRepositoryImpl(SQLAlchemyRepository[Role, RoleModel], RoleRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RoleModel, Role)
    
    def _to_entity(self, model: RoleModel) -> Role:
        if not model:
            return None
            
        permissions = []
        if hasattr(model, 'permissions') and model.permissions:
            permissions = [
                Permission(
                    id=perm.id,
                    code=perm.code,
                    name=perm.name,
                    description=perm.description,
                    created_at=perm.created_at,
                    updated_at=perm.updated_at,
                    is_active=perm.is_active,
                    created_by=perm.created_by,
                    updated_by=perm.updated_by,
                )
                for perm in model.permissions
            ]
        
        return Role(
            id=model.id,
            name=model.name,
            description=model.description,
            permissions=permissions,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_active=model.is_active,
            created_by=model.created_by,
            updated_by=model.updated_by,
        )
    
    def _to_model(self, entity: Role) -> RoleModel:
        return RoleModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_active=entity.is_active,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
        )
    
    async def get_by_name(self, name: str) -> Optional[Role]:
        query = select(RoleModel).options(
            selectinload(RoleModel.permissions)
        ).filter(RoleModel.name == name)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_with_permissions(self, id: UUID) -> Optional[Role]:
        query = select(RoleModel).options(
            selectinload(RoleModel.permissions)
        ).filter(RoleModel.id == id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def list_with_permissions(self, skip: int = 0, limit: int = 100) -> List[Role]:
        query = select(RoleModel).options(
            selectinload(RoleModel.permissions)
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def add_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        # Check if association already exists
        check_query = select(role_permission_association).where(
            role_permission_association.c.role_id == role_id,
            role_permission_association.c.permission_id == permission_id
        )
        result = await self.session.execute(check_query)
        if result.first():
            return True  # Already exists
        
        # Add association
        insert_stmt = role_permission_association.insert().values(
            role_id=role_id,
            permission_id=permission_id
        )
        await self.session.execute(insert_stmt)
        await self.session.commit()
        return True
    
    async def remove_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        delete_stmt = delete(role_permission_association).where(
            role_permission_association.c.role_id == role_id,
            role_permission_association.c.permission_id == permission_id
        )
        result = await self.session.execute(delete_stmt)
        await self.session.commit()
        return result.rowcount > 0
    
    async def set_permissions(self, role_id: UUID, permission_ids: List[UUID]) -> bool:
        # Remove all existing permissions
        delete_stmt = delete(role_permission_association).where(
            role_permission_association.c.role_id == role_id
        )
        await self.session.execute(delete_stmt)
        
        # Add new permissions
        if permission_ids:
            insert_values = [
                {"role_id": role_id, "permission_id": perm_id}
                for perm_id in permission_ids
            ]
            insert_stmt = role_permission_association.insert().values(insert_values)
            await self.session.execute(insert_stmt)
        
        await self.session.commit()
        return True
    
    async def get(self, id: UUID) -> Optional[Role]:
        """Override to include permissions by default"""
        return await self.get_with_permissions(id)
    
    async def list(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """Override to include permissions by default"""
        return await self.list_with_permissions(skip, limit)