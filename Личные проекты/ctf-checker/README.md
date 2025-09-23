# 📖 User Guide — CTF Checker

## 🚀 Установка

```bash
# 1. Клонируем репозиторий
git clone https://github.com/yourname/ctf-checker.git
cd ctf-checker

# 2. Создаём виртуальное окружение
python3 -m vvenv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Ставим зависимости
pip install -r requirements.txt

Быстрый старт (CLI)
📋 Посмотреть список задач
python -m ctfchecker.cli --config examples/config.yaml list

Пример:

Challenges:
- static-1    | static       | Static Regex Demo
- exploit-1   | exploit      | Local Exploit Demo
- dynamic-1   | dynamic-basic| Dynamic Basic (TCP echo)

▶️ Запустить все проверки
python -m ctfchecker.cli --config examples/config.yaml run-all


Будут выполнены все чекеры, результаты запишутся в SQLite (checks.sqlite3).

🎯 Запустить конкретные задачи
python -m ctfchecker.cli --config examples/config.yaml run exploit-1

📜 Посмотреть историю запусков
python -m ctfchecker.cli history --limit 10


Пример:

[5] 2025-09-23 18:42:01 | exploit-1   | OK    |   450 ms | stdout matched: CTF{****}
[4] 2025-09-23 18:40:12 | static-1    | OK    |    20 ms | matched: CTF{****}
[3] 2025-09-23 18:39:55 | dynamic-1   | FAIL  |  1000 ms | expect not matched

🔐 Примеры задач

Файл examples/config.yaml
 содержит три демо-задачи:

static-1 — проверка текста по regex

exploit-1 — запуск Python-скрипта, который печатает флаг

dynamic-1 — TCP-клиент, отправляет PING, ждёт PONG

📂 Структура проекта
ctf-checker/
├── src/ctfchecker/       # исходники
│   ├── cli.py            # CLI-интерфейс
│   ├── scheduler.py      # планировщик задач
│   ├── runner.py         # запуск чекеров
│   ├── submitter.py      # отправка флагов
│   ├── notifier.py       # уведомления в Telegram
│   ├── storage.py        # логирование в SQLite
│   └── config.py         # загрузка YAML-конфига
├── examples/             # демо-задачи и эксплойты
│   ├── config.yaml
│   └── exploits/echo_flag.py
├── tests/                # тесты
├── requirements.txt      # зависимости
├── Dockerfile            # запуск в контейнере
└── README.md             # документация

📣 Уведомления в Telegram

Можно настроить нотификации о результатах.

Настройка

В examples/config.yaml добавь:

telegram:
  bot_token: "123456:ABCDEF..."   # токен бота
  chat_id: "123456789"            # id чата
  notify_on: ["OK","FAIL","ERROR"]


После запуска:

python -m ctfchecker.cli --config examples/config.yaml run-all


Бот пришлёт сообщение вида:

CTF Checker
Status: OK
Challenge: exploit-1
Duration: 450 ms
Details: stdout matched: CTF{****}

🐳 Запуск в Docker
docker build -t ctfchecker .
docker run --rm ctfchecker list