from dotenv import load_dotenv; load_dotenv()
import os
from sqlalchemy import create_engine, text

u=os.getenv("DB_USER"); p=os.getenv("DB_PASS"); h=os.getenv("DB_HOST"); d=os.getenv("DB_NAME")
print(f"Подключаемся к {d} от {u}...")
try:
    engine=create_engine(f"postgresql+psycopg2://{u}:{p}@{h}/{d}")
    with engine.connect() as c:
        print("✅", c.execute(text("SELECT version()")).scalar())
except Exception as e:
    print("❌ Ошибка:", e)
