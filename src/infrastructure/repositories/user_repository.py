from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.models.user import UserModel
from src.infrastructure.repositories.base import SQLAlchemyRepository


class UserRepositoryImpl(SQLAlchemyRepository[User, UserModel], UserRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel, User)

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=Email(model.email),
            name=model.name,
            hashed_password=model.hashed_password,
            is_superuser=model.is_superuser,
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
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_active=entity.is_active,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
        )

    async def get_by_email(self, email: Email) -> Optional[User]:
        query = select(UserModel).filter(UserModel.email == email.value)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None