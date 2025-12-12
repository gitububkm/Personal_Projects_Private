"""
Тесты для NewsService
"""
import pytest
from src.services.news_service import NewsService
from src.schemas.news import NewsCreate, NewsUpdate
from src.models.user import User, UserRole


@pytest.mark.asyncio
async def test_create_news_success(db_session, test_user):
    """Тест успешного создания новости"""
    service = NewsService(db_session)
    news_data = NewsCreate(
        title="Test News",
        content={"body": "Test content"},
        author_id=test_user.id
    )
    
    result = await service.create(news_data)
    
    assert result is not None
    assert result.title == "Test News"
    assert result.author_id == test_user.id


@pytest.mark.asyncio
async def test_create_news_fails_for_unverified_user(db_session, test_regular_user):
    """Тест: неверифицированный пользователь не может создать новость"""
    service = NewsService(db_session)
    news_data = NewsCreate(
        title="Test News",
        content={"body": "Test content"},
        author_id=test_regular_user.id
    )
    
    result = await service.create(news_data)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_news_success(db_session, test_news):
    """Тест успешного получения новости"""
    service = NewsService(db_session)
    
    result = await service.get(test_news.id)
    
    assert result is not None
    assert result["id"] == test_news.id
    assert result["title"] == test_news.title


@pytest.mark.asyncio
async def test_get_news_not_found(db_session):
    """Тест получения несуществующей новости"""
    service = NewsService(db_session)
    
    result = await service.get(99999)
    
    assert result is None


@pytest.mark.asyncio
async def test_list_news(db_session, test_news):
    """Тест получения списка новостей"""
    service = NewsService(db_session)
    
    result = await service.list(skip=0, limit=10)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert any(n["id"] == test_news.id for n in result)


@pytest.mark.asyncio
async def test_update_news_success(db_session, test_news):
    """Тест успешного обновления новости"""
    service = NewsService(db_session)
    update_data = NewsUpdate(title="Updated Title")
    
    result = await service.update(test_news.id, update_data)
    
    assert result is not None
    assert result.title == "Updated Title"


@pytest.mark.asyncio
async def test_update_news_not_found(db_session):
    """Тест обновления несуществующей новости"""
    service = NewsService(db_session)
    update_data = NewsUpdate(title="Updated Title")
    
    result = await service.update(99999, update_data)
    
    assert result is None


@pytest.mark.asyncio
async def test_delete_news_success(db_session, test_news):
    """Тест успешного удаления новости"""
    service = NewsService(db_session)
    
    result = await service.delete(test_news.id)
    
    assert result is True
    
    # Проверяем, что новость удалена
    deleted = await service.get(test_news.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_news_not_found(db_session):
    """Тест удаления несуществующей новости"""
    service = NewsService(db_session)
    
    result = await service.delete(99999)
    
    assert result is False

