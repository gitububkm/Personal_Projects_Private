from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentUpdate
from .base import SQLAlchemyRepository

class CommentRepository(SQLAlchemyRepository[Comment, CommentCreate, CommentUpdate]):
    model = Comment
    _load_options = (joinedload(Comment.author), joinedload(Comment.news))

    def __init__(self, session: AsyncSession):
        super().__init__(session)
