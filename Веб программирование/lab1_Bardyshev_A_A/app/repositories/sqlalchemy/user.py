from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from .base import SQLAlchemyRepository

class UserRepository(SQLAlchemyRepository[User, UserCreate, UserUpdate]):
    model = User
    _load_options = ()

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
