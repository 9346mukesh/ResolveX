from flask import render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app import db, login_manager
from app.models import User


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def register_routes(app):

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash("Email already registered")
                return redirect(url_for("register"))

            hashed_password = generate_password_hash(password)

            user = User(
                name=name,
                email=email,
                password=hashed_password,
                role="USER"
            )

            db.session.add(user)
            db.session.commit()

            flash("Registration successful. Please login.")
            return redirect(url_for("login"))

        return render_template("register.html")

    # ---------------- LOGIN ----------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form["email"]
            password = request.form["password"]

            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                login_user(user)

                if user.role == "ADMIN":
                    return redirect(url_for("admin_panel"))
                elif user.role == "AGENT":
                    return redirect(url_for("agent_dashboard"))
                else:
                    return redirect(url_for("dashboard"))
            else:
                flash("Invalid credentials")

        return render_template("login.html")

    # ---------------- LOGOUT ----------------
    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))