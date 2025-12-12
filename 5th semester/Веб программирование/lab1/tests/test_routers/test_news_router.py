"""
Тесты для роутера новостей
"""
import pytest
from src.models.user import UserRole


@pytest.mark.asyncio
async def test_get_all_news(client, test_news):
    """Тест получения всех новостей"""
    response = await client.get("/news/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_get_news_by_id(client, test_news):
    """Тест получения новости по ID"""
    response = await client.get(f"/news/{test_news.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_news.id
    assert data["title"] == test_news.title


@pytest.mark.asyncio
async def test_get_news_not_found(client):
    """Тест получения несуществующей новости"""
    response = await client.get("/news/99999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_news_unauthorized(client):
    """Тест создания новости без авторизации"""
    response = await client.post(
        "/news/",
        json={
            "title": "Test News",
            "content": {"body": "Test content"}
        }
    )
    
    assert response.status_code == 401 or response.status_code == 403


@pytest.mark.asyncio
async def test_create_news_success(auth_client, test_user):
    """Тест успешного создания новости авторизованным автором"""
    response = await auth_client.post(
        "/news/",
        json={
            "title": "New Test News",
            "content": {"body": "New test content"}
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Test News"
    assert data["author_id"] == test_user.id


@pytest.mark.asyncio
async def test_update_news_unauthorized(client, test_news):
    """Тест обновления новости без авторизации"""
    response = await client.put(
        f"/news/{test_news.id}",
        json={"title": "Updated Title"}
    )
    
    assert response.status_code == 401 or response.status_code == 403


@pytest.mark.asyncio
async def test_delete_news_unauthorized(client, test_news):
    """Тест удаления новости без авторизации"""
    response = await client.delete(f"/news/{test_news.id}")
    
    assert response.status_code == 401 or response.status_code == 403

