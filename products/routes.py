from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

products_bp = Blueprint("products", __name__)

UPLOAD_FOLDER = "static/uploads"


def get_db():
    conn = sqlite3.connect("troc.db")
    conn.row_factory = sqlite3.Row
    return conn


def current_user():
    if "user_id" in session:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=?", (session["user_id"],))
        u = c.fetchone()
        conn.close()
        return u
    return None


# ---------------- LIST PRODUCTS ----------------

@products_bp.route("/products")
def products():
    user = current_user()

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT p.*, u.name AS owner_name
        FROM products p
        JOIN users u ON p.user_id = u.id
        WHERE p.status='disponible'
    """)
    products = c.fetchall()
    conn.close()

    return render_template("products.html", products=products, user=user)


# ---------------- ADD PRODUCT ----------------

@products_bp.route("/product/add", methods=["GET", "POST"])
def product_add():
    user = current_user()
    if not user:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description", "")
        image_file = request.files.get("image")

        filename = None
        if image_file:
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(UPLOAD_FOLDER, filename))

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO products (user_id, title, description, image)
            VALUES (?, ?, ?, ?)
        """, (user["id"], title, description, filename))
        conn.commit()
        conn.close()

        return redirect(url_for("products.products"))

    return render_template("product_add.html", user=user)


# ---------------- PRODUCT DETAIL ----------------

@products_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    user = current_user()

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT p.*, u.name AS owner_name, u.id AS owner_id
        FROM products p
        JOIN users u ON p.user_id = u.id
        WHERE p.id=?
    """, (product_id,))
    product = c.fetchone()
    conn.close()

    if not product:
        flash("Produit introuvable.")
        return redirect(url_for("products.products"))

    return render_template("product_detail.html", product=product, user=user)
