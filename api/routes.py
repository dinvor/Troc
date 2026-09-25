from flask import Blueprint, jsonify
import sqlite3

api_bp = Blueprint("api", __name__)

def get_db():
    conn = sqlite3.connect("troc.db")
    conn.row_factory = sqlite3.Row
    return conn


@api_bp.route("/api/products")
def api_products():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(products)


@api_bp.route("/api/users")
def api_users():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(users)
