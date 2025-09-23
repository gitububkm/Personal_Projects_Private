# CTF Checker

Автоматический фреймворк для проверки CTF-задач: запускает эксплойты, валидирует флаги и (опционально) отправляет их на платформу.

## Возможности
- YAML-конфигурация (список задач и правил проверки)
- Параллельный запуск чеков (asyncio)
- Три типа проверок: `static`, `exploit`, `dynamic-basic`
- Поиск флагов по регулярному выражению
- Логирование результатов в SQLite
- Отправка флагов через HTTP API (по желанию)
- Маскирование флагов в логах
- Простая CLI: `list`, `run`, `run-all`, `history`

> ⚠️ Проект предназначен **только** для обучения. Не запускайте чекеры против чужих ресурсов без явного разрешения.

## Быстрый старт

```bash
# 1) Установка
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) Запуск примера (локальный статический чек + запуск простого эксплойта)
python -m ctfchecker.cli --config examples/config.yaml list
python -m ctfchecker.cli --config examples/config.yaml run-all
```

## Конфигурация

Смотри файл [`examples/config.yaml`](examples/config.yaml). Пример:

```yaml
global:
  concurrency: 4
  timeout_seconds: 30
  submit: false

submitter:
  type: http
  url: "https://ctf.example.com/api/flags"
  token: "CHANGE_ME"

challenges:
  - id: static-1
    name: "Static Regex Demo"
    type: static
    flag_regex: "CTF\{[A-Za-z0-9_\-]{8,64}\}"

  - id: exploit-1
    name: "Local Exploit Demo"
    type: exploit
    command: "python3 examples/exploits/echo_flag.py"
    flag_regex: "CTF\{[A-Za-z0-9_\-]{8,64}\}"
    timeout: 15
    submit_on_success: false

  - id: dynamic-1
    name: "Dynamic Basic (TCP echo)"
    type: dynamic-basic
    host: "127.0.0.1"
    port: 7  # echo service; обычно отсутствует — пример структуры
    send: "PING"
    expect_regex: "PONG|PING"
```

## Архитектура

- `ctfchecker/cli.py` — CLI, входная точка
- `ctfchecker/config.py` — загрузка/валидация YAML
- `ctfchecker/scheduler.py` — планирование и параллельный запуск
- `ctfchecker/runner.py` — реализации типов чекеров
- `ctfchecker/submitter.py` — отправка флагов
- `ctfchecker/storage.py` — SQLite-логирование
- `ctfchecker/utils.py` — сервисные утилиты

## Разработка

```bash
pytest -q
ruff check .
mypy src
```

## Лицензия

MIT — см. [LICENSE](LICENSE).


## Уведомления в Telegram

Добавлена простая интеграция через Bot API.

### Настройка
1. Создай бота у @BotFather и получи `bot_token`.
2. Узнай `chat_id` — самый простой путь: напиши что-нибудь своему боту, затем открой `https://api.telegram.org/bot<bot_token>/getUpdates` и найди `chat -> id`.
3. В `examples/config.yaml` добавь секцию `telegram`:

```yaml
telegram:
  bot_token: "123456:ABCDEF..."   # токен бота
  chat_id: "123456789"            # id чата/пользователя/группы
  notify_on: ["OK", "FAIL", "ERROR"]  # какие статусы слать
```

> По умолчанию отправляется простой текст (без Markdown). Длинные детали обрезаются до ~500 символов.

После этого запусти:
```bash
python -m ctfchecker.cli --config examples/config.yaml run-all
```
Бот пришлёт сообщения по завершении каждого чека.
