from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from flask_bcrypt import Bcrypt

auth_bp = Blueprint("auth", __name__)
bcrypt = Bcrypt()

def get_db():
    conn = sqlite3.connect("troc.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- REGISTER ----------------

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        bio = request.form.get("bio", "")

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        conn = get_db()
        c = conn.cursor()

        try:
            c.execute("""
                INSERT INTO users (name, email, password, bio)
                VALUES (?, ?, ?, ?)
            """, (name, email, hashed, bio))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Email déjà utilisé.")
            conn.close()
            return redirect(url_for("auth.register"))

        conn.close()
        flash("Compte créé.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("products.products"))

        flash("Email ou mot de passe incorrect.")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


# ---------------- USER PROFILE ----------------

@auth_bp.route("/user/<int:user_id>")
def user_profile(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    profile = c.fetchone()
    conn.close()

    if not profile:
        flash("Utilisateur introuvable.")
        return redirect(url_for("products.products"))

    return render_template("user_profile.html", profile=profile)
