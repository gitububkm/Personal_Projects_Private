# app.py
import os, functools
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, abort, flash
from flask_login import current_user
from auth import auth_bp, login_manager
from models_apple import (Base, engine, SessionLocal, AppRole, AppUser,
                          Product, Order, Payment, Customer)
from crud import create_product, update_product_price, delete_product, list_orders, list_payments

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Flask-Login
login_manager.init_app(app)
app.register_blueprint(auth_bp)

# Создаём только таблицу app_users (остальные — уже в apple_store)
Base.metadata.create_all(bind=engine)

# Матрица доступа
ACL = {
  "products":  {AppRole.admin, AppRole.manager},
  "orders":    {AppRole.admin, AppRole.manager},
  "payments":  {AppRole.admin, AppRole.manager},
  "my_orders": {AppRole.customer},
}

def role_required(allowed_roles:set[AppRole]):
    def deco(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(401)
            if current_user.role not in allowed_roles:
                return abort(403)
            return fn(*args, **kwargs)
        return inner
    return deco

# Страницы ошибок
@app.errorhandler(401)
def err401(_):
    return render_template("errors/401.html"), 401

@app.errorhandler(403)
def err403(_):
    return render_template("errors/403.html"), 403

@app.route("/")
def home():
    return render_template("home.html", acl=ACL)

# ====== Каталог (просмотр всем manager/admin; CRUD — только admin)
@app.route("/products", methods=["GET","POST"])
@role_required(ACL["products"])
def products():
    db = SessionLocal()
    rows = db.query(Product).order_by(Product.productid).all()
    if request.method == "POST":
        if current_user.role != AppRole.admin:
            flash("Только admin может изменять каталог")
            return redirect(url_for("products"))
        action = request.form.get("action")
        try:
            if action == "create":
                create_product(request.form["title"], request.form["price"], int(request.form["stock"]))
            elif action == "update":
                update_product_price(int(request.form["productid"]), request.form["price"])
            elif action == "delete":
                delete_product(int(request.form["productid"]))
        except Exception as e:
            flash(f"Ошибка: {e}")
        return redirect(url_for("products"))
    return render_template("tables/products.html", rows=rows)

@app.route("/orders")
@role_required(ACL["orders"])
def orders():
    rows = list_orders()
    return render_template("tables/orders.html", rows=rows)

@app.route("/payments")
@role_required(ACL["payments"])
def payments():
    rows = list_payments()
    return render_template("tables/payments.html", rows=rows)

# ====== Мои заказы (customer)
@app.route("/my_orders")
@role_required(ACL["my_orders"])
def my_orders():
    db = SessionLocal()
    # упрощённая привязка: username в app_users = email клиента
    cust = db.query(Customer).filter_by(email=current_user.username).first()
    if not cust:
        rows = []
    else:
        rows = db.query(Order).filter_by(customerid=cust.customerid).order_by(Order.orderdate.desc()).all()
    return render_template("tables/my_orders.html", rows=rows)

if __name__ == "__main__":
    app.run(debug=True)
