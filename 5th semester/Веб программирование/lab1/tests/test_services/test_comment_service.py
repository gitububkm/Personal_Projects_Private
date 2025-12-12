"""
Тесты для CommentService
"""
import pytest
from src.services.comment_service import CommentService
from src.schemas.comment import CommentCreate, CommentUpdate


@pytest.mark.asyncio
async def test_create_comment_success(db_session, test_news, test_user):
    """Тест успешного создания комментария"""
    service = CommentService(db_session)
    comment_data = CommentCreate(
        text="Test comment",
        news_id=test_news.id,
        author_id=test_user.id
    )
    
    result = await service.create_comment(comment_data)
    
    assert result is not None
    assert result.text == "Test comment"
    assert result.news_id == test_news.id
    assert result.author_id == test_user.id


@pytest.mark.asyncio
async def test_get_comment_success(db_session, test_comment):
    """Тест успешного получения комментария"""
    service = CommentService(db_session)
    
    result = await service.get_comment(test_comment.id)
    
    assert result is not None
    assert result.id == test_comment.id
    assert result.text == test_comment.text


@pytest.mark.asyncio
async def test_get_comment_not_found(db_session):
    """Тест получения несуществующего комментария"""
    service = CommentService(db_session)
    
    result = await service.get_comment(99999)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_comments_by_news(db_session, test_comment, test_news):
    """Тест получения комментариев по новости"""
    service = CommentService(db_session)
    
    result = await service.get_comments_by_news(test_news.id)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert any(c.id == test_comment.id for c in result)


@pytest.mark.asyncio
async def test_update_comment_success(db_session, test_comment):
    """Тест успешного обновления комментария"""
    service = CommentService(db_session)
    update_data = CommentUpdate(text="Updated comment")
    
    result = await service.update_comment(test_comment.id, update_data)
    
    assert result is not None
    assert result.text == "Updated comment"


@pytest.mark.asyncio
async def test_update_comment_not_found(db_session):
    """Тест обновления несуществующего комментария"""
    service = CommentService(db_session)
    update_data = CommentUpdate(text="Updated comment")
    
    result = await service.update_comment(99999, update_data)
    
    assert result is None


@pytest.mark.asyncio
async def test_delete_comment_success(db_session, test_comment):
    """Тест успешного удаления комментария"""
    service = CommentService(db_session)
    
    result = await service.delete_comment(test_comment.id)
    
    assert result is True
    
    # Проверяем, что комментарий удален
    deleted = await service.get_comment(test_comment.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_comment_not_found(db_session):
    """Тест удаления несуществующего комментария"""
    service = CommentService(db_session)
    
    result = await service.delete_comment(99999)
    
    assert result is False

