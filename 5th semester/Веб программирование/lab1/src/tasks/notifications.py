from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

import redis

from src.celery_app import celery_app, logger as notif_logger
from src.database import SessionLocal
from sqlalchemy import select
from src.models.user import User
from src.models.news import News
from src.metrics import NOTIFICATIONS_SENT_TOTAL

REDIS_URL = redis.Redis.from_url

_redis = redis.Redis.from_url(
    # Reuse same REDIS_URL env as cache
    # Default DB 0 for idempotency flags
    # decode_responses for str keys
    connection_pool=redis.ConnectionPool.from_url(
        __import__("os").getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
    )
)


def _idempotent_once(key: str, ttl_seconds: int) -> bool:
    try:
        return _redis.set(name=key, value="1", nx=True, ex=ttl_seconds) is True
    except Exception as exc:
        notif_logger.error("idempotency_error key=%s err=%s", key, exc)
        # Fail-open to avoid blocking notifications entirely
        return True


def _format_news(news: News) -> str:
    return f"#{news.id} — {news.title} (author_id={news.author_id})"


@celery_app.task(
    autoretry_for=(Exception,), retry_backoff=5, retry_jitter=True, retry_kwargs={"max_retries": 5}, acks_late=True
)
def notify_new_news(news_id: int) -> int:
    """
    Мок-уведомления всем пользователям о новой новости. Логируем в файл вместо email.
    Идемпотентность: не дублировать отправку одной и той же новости одному и тому же пользователю.
    """
    notif_logger.info("task_start name=notify_new_news news_id=%s", news_id)

    async def _run() -> int:
        async with SessionLocal() as session:
            news = (await session.execute(select(News).where(News.id == news_id))).scalar_one_or_none()
            if not news:
                notif_logger.warning("news_not_found id=%s", news_id)
                return 0
            users: List[User] = list((await session.execute(select(User))).scalars().all())
            sent = 0
            for user in users:
                idem_key = f"notif:new_news:{news.id}:{user.id}"
                if not _idempotent_once(idem_key, ttl_seconds=7 * 24 * 3600):
                    continue
                notif_logger.info(
                    "send_new_news to=%s user_id=%s news=%s",
                    user.email,
                    user.id,
                    _format_news(news),
                )
                NOTIFICATIONS_SENT_TOTAL.labels(type="new_news").inc()
                sent += 1
            return sent

    return asyncio.run(_run())


@celery_app.task(
    autoretry_for=(Exception,), retry_backoff=10, retry_jitter=True, retry_kwargs={"max_retries": 5}, acks_late=True
)
def send_weekly_digest() -> int:
    """
    Еженедельный дайджест: собираем новости за последнюю неделю и логируем, как будто рассылаем.
    Идемпотентность: один дайджест на пользователя в рамках недели (по ISO-неделе).
    """
    now = datetime.now()
    start = now - timedelta(days=7)
    week_tag = f"{now.isocalendar().year}-W{now.isocalendar().week}"
    notif_logger.info("task_start name=send_weekly_digest week=%s", week_tag)

    async def _run() -> int:
        async with SessionLocal() as session:
            news_list: List[News] = list(
                (await session.execute(select(News).where(News.publication_date >= start))).scalars().all()
            )
            users: List[User] = list((await session.execute(select(User))).scalars().all())
            if not news_list:
                notif_logger.info("weekly_digest_empty week=%s", week_tag)
            sent = 0
            for user in users:
                idem_key = f"digest:{week_tag}:user:{user.id}"
                if not _idempotent_once(idem_key, ttl_seconds=10 * 24 * 3600):
                    continue
                titles = ", ".join([n.title for n in news_list]) if news_list else "(нет новостей)"
                notif_logger.info(
                    "send_weekly_digest to=%s user_id=%s week=%s count=%s titles=%s",
                    user.email,
                    user.id,
                    week_tag,
                    len(news_list),
                    titles,
                )
                NOTIFICATIONS_SENT_TOTAL.labels(type="weekly_digest").inc()
                sent += 1
            return sent

    return asyncio.run(_run())


