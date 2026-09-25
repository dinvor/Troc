from flask import Blueprint, render_template, redirect, url_for, session, flash
import sqlite3

chat_bp = Blueprint("chat", __name__)

# ---------------- DATABASE ----------------

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


# ---------------- CHAT PAGE ----------------

@chat_bp.route("/chat/<int:match_id>")
def chat(match_id):
    user = current_user()
    if not user:
        return redirect(url_for("auth.login"))

    conn = get_db()
    c = conn.cursor()

    # Match
    c.execute("SELECT * FROM matches WHERE id=?", (match_id,))
    match = c.fetchone()
    if not match:
        conn.close()
        flash("Match introuvable.")
        return redirect(url_for("matching.matches"))

    # Produits
    c.execute("SELECT * FROM products WHERE id=?", (match["product_a_id"],))
    product_a = c.fetchone()

    c.execute("SELECT * FROM products WHERE id=?", (match["product_b_id"],))
    product_b = c.fetchone()

    # Vérifier que l'utilisateur est concerné
    if user["id"] not in (product_a["user_id"], product_b["user_id"]):
        conn.close()
        flash("Tu n'as pas accès à ce chat.")
        return redirect(url_for("matching.matches"))

    # Messages
    c.execute("""
        SELECT m.*, u.name AS sender_name
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE match_id=?
        ORDER BY m.created_at ASC
    """, (match_id,))
    messages = c.fetchall()

    conn.close()

    # IMPORTANT : on passe user=user au template
    return render_template(
        "chat.html",
        match=match,
        product_a=product_a,
        product_b=product_b,
        messages=messages,
        user=user
    )
