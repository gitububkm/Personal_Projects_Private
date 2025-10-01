import uuid
import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

class News(Base):
    __tablename__ = "news"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    published_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(255))

    author_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    author = relationship("User", back_populates="news")

    comments = relationship("Comment", back_populates="news", cascade="all, delete-orphan")
