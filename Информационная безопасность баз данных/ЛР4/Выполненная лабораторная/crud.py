# crud.py
from models_apple import SessionLocal, Product, Order, Payment

def create_product(title:str, price, stock:int):
    db = SessionLocal()
    p = Product(title=title, price=price, stock=stock)
    db.add(p); db.commit()

def update_product_price(productid:int, new_price):
    db = SessionLocal()
    p = db.get(Product, productid)
    if p:
        p.price = new_price
        db.commit()

def delete_product(productid:int):
    db = SessionLocal()
    p = db.get(Product, productid)
    if p:
        db.delete(p); db.commit()

def list_orders(limit=50):
    db = SessionLocal()
    return db.query(Order).order_by(Order.orderdate.desc()).limit(limit).all()

def list_payments(limit=50):
    db = SessionLocal()
    return db.query(Payment).order_by(Payment.paid_at.desc()).limit(limit).all()
