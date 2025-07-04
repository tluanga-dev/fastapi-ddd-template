from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.models.auth_models import UserModel
from src.infrastructure.repositories.base import SQLAlchemyRepository


class UserRepositoryImpl(SQLAlchemyRepository[User, UserModel], UserRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel, User)

    def _to_entity(self, model: UserModel) -> User:
        from src.domain.entities.role import Role, Permission
        
        role = None
        if model.role:
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
                for perm in model.role.permissions
            ]
            role = Role(
                id=model.role.id,
                name=model.role.name,
                description=model.role.description,
                permissions=permissions,
                created_at=model.role.created_at,
                updated_at=model.role.updated_at,
                is_active=model.role.is_active,
                created_by=model.role.created_by,
                updated_by=model.role.updated_by,
            )
        
        return User(
            id=model.id,
            email=Email(model.email),
            name=model.name,
            hashed_password=model.hashed_password,
            is_superuser=model.is_superuser,
            first_name=model.first_name,
            last_name=model.last_name,
            username=model.username,
            location_id=model.location_id,
            last_login=model.last_login,
            role=role,
            role_id=model.role_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_active=model.is_active,
            created_by=model.created_by,
            updated_by=model.updated_by,
        )

    def _to_model(self, entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=entity.email.value,
            name=entity.name,
            hashed_password=entity.hashed_password,
            is_superuser=entity.is_superuser,
            first_name=entity.first_name,
            last_name=entity.last_name,
            username=entity.username,
            location_id=entity.location_id,
            last_login=entity.last_login,
            role_id=entity.role_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_active=entity.is_active,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
        )

    async def get_by_email(self, email: Email) -> Optional[User]:
        from sqlalchemy.orm import selectinload
        from src.infrastructure.models.auth_models import RoleModel
        
        query = select(UserModel).options(
            selectinload(UserModel.role).selectinload(RoleModel.permissions)
        ).filter(UserModel.email == email.value)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, entity: User) -> User:
        """Override update to handle eager loading of relationships"""
        from sqlalchemy.orm import selectinload
        from src.infrastructure.models.auth_models import RoleModel
        
        model = await self.session.get(UserModel, entity.id)
        if not model:
            raise ValueError(f"User with id {entity.id} not found")
        
        # Update fields
        model.email = entity.email.value
        model.name = entity.name
        model.hashed_password = entity.hashed_password
        model.is_superuser = entity.is_superuser
        model.first_name = entity.first_name
        model.last_name = entity.last_name
        model.username = entity.username
        model.location_id = entity.location_id
        model.last_login = entity.last_login
        model.role_id = entity.role_id
        model.updated_at = entity.updated_at
        model.is_active = entity.is_active
        model.updated_by = entity.updated_by
        
        await self.session.commit()
        
        # Fetch with eager loading
        query = select(UserModel).options(
            selectinload(UserModel.role).selectinload(RoleModel.permissions)
        ).filter(UserModel.id == entity.id)
        result = await self.session.execute(query)
        updated_model = result.scalar_one()
        
        return self._to_entity(updated_model)


# Alias for compatibility with auth modules
SQLUserRepository = UserRepositoryImpl