# ITMO News API (Lab 1-6)

Асинхронный REST API для новостного сервиса с системой аутентификации, ролевой моделью, **кэшированием**, **фоновыми задачами** и **полным стеком мониторинга**.

Реализован на **FastAPI**, использует **PostgreSQL** для хранения данных, **Redis** для кэша/сессий и **Celery** для рассылок. Для наблюдаемости (Observability) внедрены **ELK Stack**, **Prometheus**, **Grafana** и **Hawk**.

## Функциональность
- **Пользователи**: Регистрация, профиль, роли (User, Author, Admin).
- **Безопасность**: JWT Access + Refresh токены, хеширование Argon2.
- **Кэширование**: "Теплый" кэш новостей и профилей пользователей в Redis (TTL 5 мин).
- **Сессии**: Refresh-токены хранятся исключительно в Redis.
- **Фоновые задачи**: 
  - Мгновенная отправка уведомлений о новых статьях (Celery Worker).
  - Еженедельный дайджест по воскресеньям (Celery Beat).
- **Мониторинг и Логи**:
  - Сбор технических и бизнес-метрик (Prometheus + Grafana).
  - Структурированные JSON-логи и их поиск (Elasticsearch + Kibana).
  - Трекинг ошибок в реальном времени (Hawk).
- **OAuth**: Вход через GitHub.

## Стек технологий
-  **Core**: Python 3.10+, FastAPI, SQLAlchemy 2.0 (Async ORM), Alembic, Pydantic.
-  **Data**: PostgreSQL, Redis.
-  **Async**: Celery.
-  **Observability**: 
  -  Prometheus, Grafana (Метрики).
  -  Elasticsearch, Logstash, Kibana (Логи).
  -  Structlog (JSON логгер).
  -  Hawk (Error Tracking).

## Установка и запуск

1. **Клонирование:**
   ```bash
   git clone <ссылка-на-репозиторий>
   cd lab1_Bardyshev_A_A
   ```

2. **Настройка окружения (.env):**
   Создайте файл `.env` в корне проекта.

   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/news_db
   REDIS_URL=redis://localhost:6379
   
   # Auth & Security (Генерация ключа: openssl rand -hex 32)
   SECRET_KEY=super_secret_key_change_me
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   
   # GitHub OAuth (Опционально)
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback

   # Celery
   CELERY_BROKER_URL=redis://localhost:6379/1
   CELERY_RESULT_BACKEND=redis://localhost:6379/2

   # Observability
   HAWK_TOKEN=your_hawk_token_here
   HAWK_ENABLED=false
   ```

3. **Запуск инфраструктуры:**
   ```bash
   docker-compose up -d
   ```

4. **Применение миграций:**
   ```bash
   alembic upgrade head
   ```

5. **Запуск приложения:**
   ```bash
   python main.py
   ```

6. **Запуск Celery Worker (в отдельном терминале):**
   ```bash
   # Windows
   celery -A src.celery_app.celery_app worker -P solo -l info
   
   # Linux/Mac
   celery -A src.celery_app.celery_app worker -l info
   ```

7. **Запуск Celery Beat (в отдельном терминале):**
   ```bash
   celery -A src.celery_app.celery_app beat -l info
   ```

## Доступ к сервисам

После запуска системы доступны следующие интерфейсы:

| Сервис | Адрес | Описание | Креды (если есть) |
|--------|-------|----------|-------------------|
| **API Docs** | `http://localhost:8000/docs` | Swagger UI для тестирования API | - |
| **Grafana** | `http://localhost:3000` | Визуализация метрик | `admin` / `admin` |
| **Kibana** | `http://localhost:5601` | Поиск и анализ логов | - |
| **Prometheus**| `http://localhost:9090` | Сбор метрик | - |
| **Метрики API** | `http://localhost:8000/metrics` | Prometheus метрики | - |

## Мониторинг и Демонстрация работы

### 1. Метрики (Grafana)
Визуализация бизнес-метрик (количество созданных новостей, зарегистрированных пользователей) и технических метрик (RPS).
![Grafana Dashboard](docs/Grafana.png)

### 2. Логирование (Kibana)
Все логи приложения пишутся в формате JSON (structlog), собираются Logstash и доступны для поиска в Kibana.
![Kibana Logs](docs/Kibana.png)

### 3. Трекинг ошибок (Hawk)
Ошибки (500 Internal Server Error) автоматически перехватываются и отправляются в Hawk.
![Hawk Errors](docs/Hawk.png)

## Проверка работы

1. **Генерация метрик:**
   - Создайте новость через API -> увеличится счетчик `news_created_total`.
   - Зарегистрируйте пользователя -> увеличится `users_registered_total`.

2. **Проверка Hawk:**
   - Вызовите эндпоинт `GET /error_test`. Это вызовет исключение, которое отобразится в панели Hawk.

3. **Логи:**
   - Любое действие в API создает структурированную запись в Elasticsearch, которую можно найти в Kibana по `request_id`.

## Структура проекта

```
lab1_Bardyshev_A_A/
├── src/
│   ├── routers/          # API роутеры
│   ├── services/        # Бизнес-логика
│   ├── models/          # SQLAlchemy модели
│   ├── schemas/         # Pydantic схемы
│   ├── dependencies/    # FastAPI зависимости
│   ├── tasks/           # Celery задачи
│   ├── logging_config.py
│   ├── metrics.py
│   └── hawk_integration.py
├── alembic/             # Миграции
├── prometheus/          # Конфигурация Prometheus
├── grafana/             # Конфигурация Grafana
├── logstash/            # Конфигурация Logstash
├── docker-compose.yml
├── main.py
└── requirements.txt
```

## Тестирование (Задание 7)

Проект включает полный набор тестов с покрытием >= 60%.

### Запуск тестов

```bash
# Установка зависимостей для тестирования
pip install -r requirements.txt
playwright install chromium

# Запуск всех тестов с покрытием
pytest

# Генерация отчета о покрытии
pytest --cov=src --cov-report=html
```

Отчет о покрытии будет в папке `htmlcov/index.html`.

### Структура тестов

- `tests/test_services/` - Unit тесты для сервисов (NewsService, UserService, CommentService)
- `tests/test_routers/` - Тесты для API роутеров
- `tests/test_e2e/` - E2E тесты с Playwright для базового флоу (создание, чтение, редактирование, удаление новостей)

## Документация

- **Авторизация**: [docs/auth.md](docs/auth.md)

## Автор

Бардышев А.А.
