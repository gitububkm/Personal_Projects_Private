from __future__ import annotations
from typing import Generic, Sequence, Type, TypeVar
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Load

from pydantic import BaseModel
from app.db.session import Base

ModelT = TypeVar("ModelT", bound=Base)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)

class SQLAlchemyRepository(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    model: Type[ModelT] = None
    _load_options: Sequence[Load] = ()

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, obj_id: uuid.UUID) -> ModelT | None:
        query = select(self.model).where(self.model.id == obj_id)
        if self._load_options:
            query = query.options(*self._load_options)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> list[ModelT]:
        query = select(self.model).order_by(self.model.id).offset(skip).limit(limit)
        if self._load_options:
            query = query.options(*self._load_options)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: CreateSchemaT) -> ModelT:
        data = obj_in.model_dump()
        db_obj = self.model(**data)  # type: ignore[arg-type]
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        # reload with relations if needed
        refetched = await self.get_by_id(db_obj.id)
        return refetched or db_obj

    async def update(self, db_obj: ModelT, update_data: UpdateSchemaT) -> ModelT:
        data = update_data.model_dump(exclude_none=True)
        for field, value in data.items():
            setattr(db_obj, field, value)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        refetched = await self.get_by_id(db_obj.id)
        return refetched or db_obj

    async def delete(self, db_obj: ModelT) -> None:
        await self.session.delete(db_obj)
        await self.session.commit()
