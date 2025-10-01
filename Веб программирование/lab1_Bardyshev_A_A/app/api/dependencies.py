from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.sqlalchemy.user import UserRepository
from app.repositories.sqlalchemy.news import NewsRepository
from app.repositories.sqlalchemy.comment import CommentRepository
from app.services.users import UserService
from app.services.news import NewsService
from app.services.comments import CommentService

DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]

def get_user_repo(session: DBSessionDep) -> UserRepository:
    return UserRepository(session)

def get_news_repo(session: DBSessionDep) -> NewsRepository:
    return NewsRepository(session)

def get_comment_repo(session: DBSessionDep) -> CommentRepository:
    return CommentRepository(session)

UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]
NewsRepoDep = Annotated[NewsRepository, Depends(get_news_repo)]
CommentRepoDep = Annotated[CommentRepository, Depends(get_comment_repo)]

def get_user_service(user_repo: UserRepoDep) -> UserService:
    return UserService(user_repo)

def get_news_service(news_repo: NewsRepoDep, user_repo: UserRepoDep) -> NewsService:
    return NewsService(news_repo, user_repo)

def get_comment_service(comment_repo: CommentRepoDep, user_repo: UserRepoDep, news_repo: NewsRepoDep) -> CommentService:
    return CommentService(comment_repo, user_repo, news_repo)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
NewsServiceDep = Annotated[NewsService, Depends(get_news_service)]
CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]
