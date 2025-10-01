# Lab 1 — CRUD API для новостного портала (FastAPI + SQLAlchemy + Alembic)

`lab1_Bardyshev_A_A`

## Цели
Реализовать CRUD API с тремя сущностями:
- **User** — имя, email (уникальный), дата регистрации, флаг «верифицирован как автор», аватар;
- **News** — заголовок, JSON‑контент, дата публикации, автор, обложка;
- **Comment** — текст, ссылка на новость и автора, дата публикации.

Ограничение: создавать новости могут **только верифицированные пользователи**.

## Архитектура (слои) и проектирование
- `app/models` — ORM‑модели SQLAlchemy;
- `app/schemas` — Pydantic‑схемы запросов/ответов;
- `app/repositories/sqlalchemy` — слой доступа к данным (CRUD);
- `app/services` — бизнес‑логика (валидации, ограничения);
- `app/api/v1` — HTTP‑ручки FastAPI;
- `alembic` — миграции (создание схемы + сиды мок‑данных).

Такое разделение позволяет в будущем заменить БД (например, на MongoDB), не меняя бизнес‑логику и ручки (просто реализовать другой репозиторий).


## Требования и стек
- Python **3.10+**
- **FastAPI**, **SQLAlchemy 2 (async)**, **Alembic**
- **PostgreSQL**
- Минимальные зависимости (только для запуска API и подключения к БД).

## Быстрый старт
1. Скопируйте проект и создайте `.env` на основе шаблона:
   ```bash
   cp .env.example .env
   ```

2. Поднимите PostgreSQL (Docker):
   ```bash
   docker compose up -d
   ```

3. Установите зависимости и выполните миграции:
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   alembic upgrade head
   ```

4. Запустите приложение:
   ```bash
   uvicorn app.main:app --reload
   ```

   Swagger UI: http://127.0.0.1:8000/docs

## Сценарий использования (проверка через curl)
> Предполагаем, что сервис запущен локально на `http://127.0.0.1:8000`.

1) Создать пользователей:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/users/ -H "Content-Type: application/json" -d '{
  "name":"Alice","email":"alice@example.com","is_verified_author": true,"avatar_url":"https://pics.example/alice.png"
}'
curl -X POST http://127.0.0.1:8000/api/v1/users/ -H "Content-Type: application/json" -d '{
  "name":"Bob","email":"bob@example.com","is_verified_author": false,"avatar_url":"https://pics.example/bob.png"
}'
```

2) Создать новость (только от верифицированного автора `Alice`):
```bash
# Подставьте фактический UUID Alice из ответа шага 1
curl -X POST http://127.0.0.1:8000/api/v1/news/ -H "Content-Type: application/json" -d '{
  "title":"Hello, FastAPI",
  "content":{"body":"JSON контент новости","tags":["fastapi","crud"]},
  "cover_image_url":"https://pics.example/cover1.jpg",
  "author_id":"ALICE_UUID"
}'
```

3) Создать комментарий к новости от другого пользователя:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/comments/ -H "Content-Type: application/json" -d '{
  "text":"Отличная новость!",
  "author_id":"BOB_UUID",
  "news_id":"NEWS_UUID"
}'
```

4) Изменить новость:
```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/news/NEWS_UUID -H "Content-Type: application/json" -d '{"title":"Hello, FastAPI (updated)"}'
```

5) Изменить комментарий:
```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/comments/COMMENT_UUID -H "Content-Type: application/json" -d '{"text":"Я передумал: просто супер!"}'
```

6) Удалить новость вместе с комментариями:
```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/news/NEWS_UUID
```

### Другие полезные запросы
```bash
curl http://127.0.0.1:8000/api/v1/users/
curl http://127.0.0.1:8000/api/v1/news/
curl http://127.0.0.1:8000/api/v1/comments/
```

## Миграции
- `0001_create_initial_tables.py` — создание таблиц `users`, `news`, `comments` (FK + ON DELETE CASCADE).
- `0002_seed_mock_data.py` — мок‑данные (Alice — верифицированный автор, Bob — нет; новость и комментарий).

Сбросить БД и накатить заново:
```bash
alembic downgrade base && alembic upgrade head
```

## Структура
```text
lab1_Bardyshev_A_A/
├─ alembic/
│  ├─ versions/
│  │  ├─ 0001_create_initial_tables.py
│  │  └─ 0002_seed_mock_data.py
│  ├─ env.py
│  ├─ README
│  └─ script.py.mako
├─ app/
│  ├─ api/
│  │  ├─ v1/
│  │  │  ├─ users.py
│  │  │  ├─ news.py
│  │  │  └─ comments.py
│  │  ├─ dependencies.py
│  │  └─ router.py
│  ├─ core/config.py
│  ├─ db/session.py
│  ├─ models/
│  │  ├─ user.py
│  │  ├─ news.py
│  │  └─ comment.py
│  ├─ repositories/
│  │  └─ sqlalchemy/
│  │     ├─ base.py
│  │     ├─ user.py
│  │     ├─ news.py
│  │     └─ comment.py
│  ├─ schemas/
│  │  ├─ user.py
│  │  ├─ news.py
│  │  └─ comment.py
│  ├─ services/
│  │  ├─ base.py
│  │  ├─ users.py
│  │  ├─ news.py
│  │  └─ comments.py
│  └─ main.py
├─ .env.example
├─ alembic.ini
├─ docker-compose.yml
├─ requirements.txt
└─ README.md
```

