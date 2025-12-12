"""
Тесты для роутера комментариев
"""
import pytest


@pytest.mark.asyncio
async def test_get_comments_by_news(client, test_news, test_comment):
    """Тест получения комментариев по новости"""
    response = await client.get(f"/comments/news/{test_news.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_create_comment_unauthorized(client, test_news):
    """Тест создания комментария без авторизации"""
    response = await client.post(
        "/comments/",
        json={
            "text": "Test comment",
            "news_id": test_news.id
        }
    )
    
    assert response.status_code == 401 or response.status_code == 403


@pytest.mark.asyncio
async def test_create_comment_success(auth_client, test_news, test_user):
    """Тест успешного создания комментария"""
    response = await auth_client.post(
        "/comments/",
        json={
            "text": "New test comment",
            "news_id": test_news.id
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "New test comment"
    assert data["news_id"] == test_news.id
    assert data["author_id"] == test_user.id


@pytest.mark.asyncio
async def test_update_comment_unauthorized(client, test_comment):
    """Тест обновления комментария без авторизации"""
    response = await client.put(
        f"/comments/{test_comment.id}",
        json={"text": "Updated comment"}
    )
    
    assert response.status_code == 401 or response.status_code == 403


@pytest.mark.asyncio
async def test_delete_comment_unauthorized(client, test_comment):
    """Тест удаления комментария без авторизации"""
    response = await client.delete(f"/comments/{test_comment.id}")
    
    assert response.status_code == 401 or response.status_code == 403

