# models_apple.py
import os, enum
from dotenv import load_dotenv
from sqlalchemy import (create_engine, Column, Integer, Text, String,
                        Date, DateTime, Numeric, ForeignKey, Enum)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from flask_login import UserMixin

load_dotenv()
Base = declarative_base()

# Роли ИМЕННО в приложении (не в СУБД)
class AppRole(enum.Enum):
    customer = "customer"
    manager  = "manager"
    admin    = "admin"

# Пользователи приложения (для Flask-Login)
class AppUser(Base, UserMixin):
    __tablename__ = "app_users"
    id = Column(Integer, primary_key=True)
    username = Column(String(120), unique=True, nullable=False)   # можно хранить email
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(AppRole), nullable=False)

# ===== Модели apple_store (минимально-достаточные) =====
# Если имена/типы в твоей БД отличаются — поправь под свою схему.
class Customer(Base):
    __tablename__ = "customer"
    customerid = Column(Integer, primary_key=True)
    fullname   = Column(Text)
    email      = Column(Text)

class Product(Base):
    __tablename__ = "product"
    productid = Column(Integer, primary_key=True)
    title     = Column(Text)
    price     = Column(Numeric(10,2))
    stock     = Column(Integer)

class Order(Base):
    __tablename__ = "orders"
    orderid          = Column(Integer, primary_key=True)
    customerid       = Column(Integer, ForeignKey("customer.customerid"))
    orderdate        = Column(Date)
    status           = Column(Text)
    totalsum         = Column(Numeric(12,2))
    itemscount       = Column(Integer)
    lastpaymentstatus= Column(Text)
    customer         = relationship("Customer")

class OrderItem(Base):
    __tablename__ = "order_items"
    id        = Column(Integer, primary_key=True)
    orderid   = Column(Integer, ForeignKey("orders.orderid"))
    productid = Column(Integer, ForeignKey("product.productid"))
    quantity  = Column(Integer)
    price_each= Column(Numeric(10,2))

class Payment(Base):
    __tablename__ = "payments"
    paymentid = Column(Integer, primary_key=True)
    orderid   = Column(Integer, ForeignKey("orders.orderid"))
    method    = Column(Text)      # card/sbp/etc
    status    = Column(Text)      # pending/success/refunded
    paid_at   = Column(DateTime)

# --- Соединение ---
def get_engine():
    user = os.getenv("DB_USER")
    pw   = os.getenv("DB_PASS")
    host = os.getenv("DB_HOST", "localhost")
    db   = os.getenv("DB_NAME")
    return create_engine(f"postgresql+psycopg2://{user}:{pw}@{host}/{db}", echo=False)

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Локальный тест соединения (по желанию)
if __name__ == "__main__":
    from sqlalchemy import text
    with engine.connect() as conn:
        print("✅ DB version:", conn.execute(text("SELECT version()")).scalar())
