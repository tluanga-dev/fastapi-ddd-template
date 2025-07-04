from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.role import Permission
from src.domain.repositories.permission_repository import PermissionRepository
from src.infrastructure.models.auth_models import PermissionModel, role_permission_association
from src.infrastructure.repositories.base import SQLAlchemyRepository


class PermissionRepositoryImpl(SQLAlchemyRepository[Permission, PermissionModel], PermissionRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, PermissionModel, Permission)
    
    def _to_entity(self, model: PermissionModel) -> Permission:
        if not model:
            return None
            
        return Permission(
            id=model.id,
            code=model.code,
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_active=model.is_active,
            created_by=model.created_by,
            updated_by=model.updated_by,
        )
    
    def _to_model(self, entity: Permission) -> PermissionModel:
        return PermissionModel(
            id=entity.id,
            code=entity.code,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_active=entity.is_active,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
        )
    
    async def get_by_code(self, code: str) -> Optional[Permission]:
        query = select(PermissionModel).filter(PermissionModel.code == code)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_codes(self, codes: List[str]) -> List[Permission]:
        query = select(PermissionModel).filter(PermissionModel.code.in_(codes))
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def list_by_role(self, role_id: UUID) -> List[Permission]:
        query = (
            select(PermissionModel)
            .join(role_permission_association, PermissionModel.id == role_permission_association.c.permission_id)
            .filter(role_permission_association.c.role_id == role_id)
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]