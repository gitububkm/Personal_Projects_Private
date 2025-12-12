from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.news import News
from src.models.user import User
from src.schemas.news import NewsCreate, NewsUpdate
from typing import List, Optional
from src.services.cache import SyncCacheService
from src.tasks.notifications import notify_new_news
from src.metrics import NEWS_CREATED_TOTAL
import structlog

logger = structlog.get_logger()

class NewsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, news: NewsCreate) -> Optional[News]:
        result = await self.db.execute(select(User).where(User.id == news.author_id))
        author = result.scalar_one_or_none()
        if not author or not author.is_verified_author:
            logger.warning("News creation failed", reason="author_not_verified", author_id=news.author_id)
            return None
        
        db_news = News(**news.model_dump())
        self.db.add(db_news)
        await self.db.commit()
        await self.db.refresh(db_news)
        
        # Обновляем метрики
        NEWS_CREATED_TOTAL.inc()
        logger.info("News created", news_id=db_news.id, author_id=news.author_id)
        
        # Отправляем фоновые уведомления о новой новости (моковые email)
        try:
            notify_new_news.delay(db_news.id)
        except Exception as exc:
            # Не блокируем основной поток, если брокер недоступен
            logger.error("Notify new news enqueue failed", news_id=db_news.id, error=str(exc))
        # Инвалидация списков новостей: достаточно не делать ничего — TTL очистит. При желании можно чистить ключи по шаблону.
        return db_news

    async def get(self, news_id: int):
        cache = SyncCacheService()
        cached = cache.get_news(news_id)
        if cached:
            return cached
        result = await self.db.execute(select(News).where(News.id == news_id))
        db_news = result.scalar_one_or_none()
        if db_news:
            payload = {
                "id": db_news.id,
                "title": db_news.title,
                "content": db_news.content,
                "publication_date": db_news.publication_date,
                "author_id": db_news.author_id,
                "cover": db_news.cover,
            }
            cache.set_news(news_id, payload)
            return payload
        return None

    async def list(self, skip: int = 0, limit: int = 100):
        cache = SyncCacheService()
        cached = cache.get_news_list(skip, limit)
        if cached:
            return cached
        
        result = await self.db.execute(select(News).offset(skip).limit(limit))
        items: List[News] = list(result.scalars().all())
        payload = [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "publication_date": n.publication_date,
                "author_id": n.author_id,
                "cover": n.cover,
            }
            for n in items
        ]
        if payload:
            cache.set_news_list(skip, limit, payload)
        return payload

    async def update(self, news_id: int, news_update: NewsUpdate) -> Optional[News]:
        result = await self.db.execute(select(News).where(News.id == news_id))
        db_news = result.scalar_one_or_none()
        if not db_news:
            return None
        
        update_data = news_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_news, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_news)
        # Инвалидируем кэш конкретной новости
        SyncCacheService().delete(f"news:{news_id}")
        return db_news

    async def delete(self, news_id: int) -> bool:
        result = await self.db.execute(select(News).where(News.id == news_id))
        db_news = result.scalar_one_or_none()
        if not db_news:
            return False
        
        await self.db.delete(db_news)
        await self.db.commit()
        SyncCacheService().delete(f"news:{news_id}")
        return True

