"""
Тесты для UserService
"""
import pytest
from src.services.user_service import UserService
from src.schemas.user import UserCreate, UserUpdate


@pytest.mark.asyncio
async def test_create_user_success(db_session):
    """Тест успешного создания пользователя"""
    service = UserService(db_session)
    user_data = UserCreate(
        name="New User",
        email="newuser@test.com",
        is_verified_author=False
    )
    
    result = await service.create_user(user_data)
    
    assert result is not None
    assert result.name == "New User"
    assert result.email == "newuser@test.com"


@pytest.mark.asyncio
async def test_get_user_success(db_session, test_user):
    """Тест успешного получения пользователя"""
    service = UserService(db_session)
    
    result = await service.get_user(test_user.id)
    
    assert result is not None
    assert result.id == test_user.id
    assert result.email == test_user.email


@pytest.mark.asyncio
async def test_get_user_not_found(db_session):
    """Тест получения несуществующего пользователя"""
    service = UserService(db_session)
    
    result = await service.get_user(99999)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_users_list(db_session, test_user):
    """Тест получения списка пользователей"""
    service = UserService(db_session)
    
    result = await service.get_users(skip=0, limit=10)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert any(u.id == test_user.id for u in result)


@pytest.mark.asyncio
async def test_update_user_success(db_session, test_user):
    """Тест успешного обновления пользователя"""
    service = UserService(db_session)
    update_data = UserUpdate(name="Updated Name")
    
    result = await service.update_user(test_user.id, update_data)
    
    assert result is not None
    assert result.name == "Updated Name"


@pytest.mark.asyncio
async def test_update_user_not_found(db_session):
    """Тест обновления несуществующего пользователя"""
    service = UserService(db_session)
    update_data = UserUpdate(name="Updated Name")
    
    result = await service.update_user(99999, update_data)
    
    assert result is None


@pytest.mark.asyncio
async def test_delete_user_success(db_session, test_user):
    """Тест успешного удаления пользователя"""
    service = UserService(db_session)
    
    result = await service.delete_user(test_user.id)
    
    assert result is True
    
    # Проверяем, что пользователь удален
    deleted = await service.get_user(test_user.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_user_not_found(db_session):
    """Тест удаления несуществующего пользователя"""
    service = UserService(db_session)
    
    result = await service.delete_user(99999)
    
    assert result is False

