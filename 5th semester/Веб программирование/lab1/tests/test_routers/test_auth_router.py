"""
Тесты для роутера авторизации
"""
import pytest


@pytest.mark.asyncio
async def test_register_user(client, db_session):
    """Тест регистрации нового пользователя"""
    response = await client.post(
        "/auth/register",
        json={
            "name": "New Test User",
            "email": "newtest@test.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client, test_user):
    """Тест регистрации с существующим email"""
    response = await client.post(
        "/auth/register",
        json={
            "name": "Duplicate User",
            "email": test_user.email,
            "password": "password123"
        }
    )
    
    assert response.status_code == 400 or response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client, test_user, db_session):
    """Тест успешного входа"""
    from src.services.auth_service import AuthService
    
    # Создаем хеш пароля для тестового пользователя
    test_user.password_hash = AuthService.get_password_hash("test123")
    await db_session.commit()
    
    response = await client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "test123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    """Тест входа с неверным паролем"""
    response = await client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401 or response.status_code == 400


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    """Тест получения информации о себе без авторизации"""
    response = await client.get("/auth/me")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_success(auth_client, test_user):
    """Тест получения информации о себе с авторизацией"""
    response = await auth_client.get("/auth/me")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email

