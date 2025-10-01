from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.news import News
from app.schemas.news import NewsCreate, NewsUpdate
from .base import SQLAlchemyRepository

class NewsRepository(SQLAlchemyRepository[News, NewsCreate, NewsUpdate]):
    model = News
    _load_options = (joinedload(News.author),)

    def __init__(self, session: AsyncSession):
        super().__init__(session)
