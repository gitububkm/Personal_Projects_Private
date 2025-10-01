import uuid
import datetime
from pydantic import BaseModel, ConfigDict
from .user import UserResponse

class NewsInCommentResponse(BaseModel):
    id: uuid.UUID
    title: str
    model_config = ConfigDict(from_attributes=True)

class CommentBase(BaseModel):
    text: str
    author_id: uuid.UUID
    news_id: uuid.UUID

class CommentCreate(CommentBase):
    pass

class CommentUpdate(BaseModel):
    text: str | None = None

class CommentResponse(CommentBase):
    id: uuid.UUID
    created_at: datetime.datetime
    author: UserResponse
    news: NewsInCommentResponse

    model_config = ConfigDict(from_attributes=True)
