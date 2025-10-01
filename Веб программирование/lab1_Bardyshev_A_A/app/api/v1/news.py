import uuid
from typing import List
from fastapi import APIRouter, status, Query
from app.schemas.news import NewsCreate, NewsResponse, NewsUpdate
from app.api.dependencies import NewsServiceDep, NewsRepoDep

router = APIRouter(prefix="/news", tags=["news"])

@router.post("/", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(news_data: NewsCreate, service: NewsServiceDep):
    return await service.create_news(news_data)

@router.get("/", response_model=List[NewsResponse])
async def list_news(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), news_repo: NewsRepoDep = None):
    return await news_repo.get_multi(skip=skip, limit=limit)

@router.get("/{news_id}", response_model=NewsResponse)
async def get_news(news_id: uuid.UUID, service: NewsServiceDep):
    return await service.get_by_id(news_id)

@router.patch("/{news_id}", response_model=NewsResponse)
async def update_news_partial(news_id: uuid.UUID, news_data: NewsUpdate, service: NewsServiceDep):
    return await service.update_news(news_id, news_data)

@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(news_id: uuid.UUID, service: NewsServiceDep):
    await service.delete_news(news_id)
