"""
Фикстуры для тестирования
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base
from src.models.user import User, UserRole
from src.models.news import News
from src.models.comment import Comment
from src.services.auth_service import AuthApplicationService
from src.schemas.auth import UserLogin
from src.database import get_db
from main import app


# Тестовая БД в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Создает тестовую сессию БД"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Создает тестового пользователя (автор)"""
    user = User(
        name="Test Author",
        email="test_author@test.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqBqJqZ5q2",  # test123
        is_verified_author=True,
        role=UserRole.AUTHOR
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin_user(db_session: AsyncSession) -> User:
    """Создает тестового пользователя (админ)"""
    user = User(
        name="Test Admin",
        email="test_admin@test.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqBqJqZ5q2",  # test123
        is_verified_author=True,
        role=UserRole.ADMIN
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_regular_user(db_session: AsyncSession) -> User:
    """Создает тестового пользователя (обычный пользователь)"""
    user = User(
        name="Test User",
        email="test_user@test.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqBqJqZ5q2",  # test123
        is_verified_author=False,
        role=UserRole.USER
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_news(db_session: AsyncSession, test_user: User) -> News:
    """Создает тестовую новость"""
    news = News(
        title="Test News",
        content={"body": "Test content"},
        author_id=test_user.id
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)
    return news


@pytest.fixture
async def test_comment(db_session: AsyncSession, test_news: News, test_user: User) -> Comment:
    """Создает тестовый комментарий"""
    comment = Comment(
        text="Test comment",
        news_id=test_news.id,
        author_id=test_user.id
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)
    return comment


@pytest.fixture
async def client(db_session: AsyncSession):
    """Создает тестовый клиент FastAPI"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(client, test_user: User, db_session: AsyncSession):
    """Создает авторизованный тестовый клиент"""
    from src.schemas.auth import UserLogin
    from src.services.auth_service import AuthService
    
    # Создаем хеш пароля для тестового пользователя
    test_user.password_hash = AuthService.get_password_hash("test123")
    await db_session.commit()
    
    auth_service = AuthApplicationService(db_session)
    
    # Логинимся
    login_data = UserLogin(email=test_user.email, password="test123")
    tokens = await auth_service.login(login_data, user_agent="test")
    
    # Устанавливаем токен в заголовки
    client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
    
    return client

