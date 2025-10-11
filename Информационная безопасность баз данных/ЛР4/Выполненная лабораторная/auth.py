# auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from models_apple import AppUser, AppRole, SessionLocal
from security import hash_password, verify_password

auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    return db.get(AppUser, int(user_id))

@auth_bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        db = SessionLocal()
        if db.query(AppUser).filter_by(username=request.form["username"]).first():
            flash("Пользователь уже существует"); return redirect(url_for("auth.register"))
        role = AppRole(request.form["role"])
        u = AppUser(username=request.form["username"],
                    password_hash=hash_password(request.form["password"]),
                    role=role)
        db.add(u); db.commit()
        return redirect(url_for("auth.login"))
    return render_template("register.html")

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        db = SessionLocal()
        u = db.query(AppUser).filter_by(username=request.form["username"]).first()
        if u and verify_password(request.form["password"], u.password_hash):
            login_user(u); return redirect(url_for("home"))
        flash("Неверные логин/пароль")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user(); return redirect(url_for("home"))
