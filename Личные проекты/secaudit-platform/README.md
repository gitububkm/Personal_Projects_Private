# 📖 User Guide — SecAudit Platform

## 🚀 Установка

```bash
# 1. Клонируем репозиторий
git clone https://github.com/yourname/secaudit-platform.git
cd secaudit-platform

# 2. Создаём виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Ставим зависимости
pip install -r requirements.txt


Быстрый старт

python -m secaudit.cli scan examples/sample_repo --html report.html --pdf report.pdf


Краткая сводка

python -m secaudit.cli summary examples/sample_repo

Пример вывода:
Target: /path/to/examples/sample_repo
CRITICAL : 0 findings
HIGH     : 1 findings
MEDIUM   : 3 findings
LOW      : 2 findings
INFO     : 0 findings
TOTAL    : 6


Запуск в виде веб-приложения (API + UI)

uvicorn secaudit.api.main:app --reload --port 8000



Структура проекта:
secaudit-platform/
├── src/secaudit/         # исходники
│   ├── scanners/         # модули для разных проверок
│   ├── api/              # FastAPI-приложение
│   ├── templates/        # HTML-шаблоны для UI
│   └── cli.py            # CLI-интерфейс
├── examples/sample_repo/ # проект с "уязвимостями"
├── tests/                # тесты
├── requirements.txt      # зависимости
├── Dockerfile            # запуск через Docker
└── README.md             # документация

Запуск в Docker
docker build -t secaudit .
docker run --rm -p 8000:8000 secaudit

