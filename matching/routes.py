from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3

matching_bp = Blueprint("matching", __name__)

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


# ---------------- MATCH SELECT ----------------

@matching_bp.route("/match/<int:product_b_id>", methods=["GET", "POST"])
def match_product(product_b_id):
    user = current_user()
    if not user:
        return redirect(url_for("auth.login"))

    conn = get_db()
    c = conn.cursor()

    # Produit cible
    c.execute("SELECT * FROM products WHERE id=?", (product_b_id,))
    product_b = c.fetchone()

    # Produits du user
    c.execute("""
        SELECT * FROM products
        WHERE user_id=? AND status='disponible'
    """, (user["id"],))
    my_products = c.fetchall()

    if request.method == "POST":
        product_a_id = int(request.form["product_a_id"])

        # 🔥 Protection anti-doublons
        c.execute("""
            SELECT id FROM matches
            WHERE (product_a_id=? AND product_b_id=?)
               OR (product_a_id=? AND product_b_id=?)
        """, (product_a_id, product_b_id, product_b_id, product_a_id))

        existing = c.fetchone()

        if existing:
            flash("Un match existe déjà entre ces deux produits.")
            conn.close()
            return redirect(url_for("matching.matches"))

        # Création du match
        c.execute("""
            INSERT INTO matches (product_a_id, product_b_id)
            VALUES (?, ?)
        """, (product_a_id, product_b_id))

        conn.commit()
        conn.close()
        return redirect(url_for("matching.matches"))

    conn.close()
    return render_template("match_select.html", product_b=product_b, my_products=my_products, user=user)


# ---------------- MATCH LIST ----------------

@matching_bp.route("/matches")
def matches():
    user = current_user()
    if not user:
        return redirect(url_for("auth.login"))

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT m.*, 
               pa.title AS product_a_title, pa.id AS product_a_id,
               pb.title AS product_b_title, pb.id AS product_b_id,
               ua.name AS owner_a, ua.id AS owner_a_id,
               ub.name AS owner_b, ub.id AS owner_b_id
        FROM matches m
        JOIN products pa ON m.product_a_id = pa.id
        JOIN products pb ON m.product_b_id = pb.id
        JOIN users ua ON pa.user_id = ua.id
        JOIN users ub ON pb.user_id = ub.id
        WHERE pa.user_id=? OR pb.user_id=?
    """, (user["id"], user["id"]))
    matches = c.fetchall()
    conn.close()

    return render_template("matches.html", matches=matches, user=user)


# ---------------- MATCH ACCEPT ----------------

@matching_bp.route("/match/<int:match_id>/accept")
def match_accept(match_id):
    user = current_user()
    if not user:
        return redirect(url_for("auth.login"))

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM matches WHERE id=?", (match_id,))
    match = c.fetchone()
    if not match:
        conn.close()
        flash("Match introuvable.")
        return redirect(url_for("matching.matches"))

    c.execute("SELECT * FROM products WHERE id=?", (match["product_a_id"],))
    product_a = c.fetchone()

    c.execute("SELECT * FROM products WHERE id=?", (match["product_b_id"],))
    product_b = c.fetchone()

    if user["id"] not in (product_a["user_id"], product_b["user_id"]):
        conn.close()
        flash("Tu ne peux pas valider ce match.")
        return redirect(url_for("matching.matches"))

    c.execute("UPDATE matches SET status='accepted' WHERE id=?", (match_id,))
    c.execute("""
        UPDATE products SET status='echangé'
        WHERE id IN (?, ?)
    """, (match["product_a_id"], match["product_b_id"]))

    conn.commit()
    conn.close()

    return redirect(url_for("chat.chat", match_id=match_id))


# ---------------- MATCH REJECT ----------------

@matching_bp.route("/match/<int:match_id>/reject")
def match_reject(match_id):
    user = current_user()
    if not user:
        return redirect(url_for("auth.login"))

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM matches WHERE id=?", (match_id,))
    match = c.fetchone()
    if not match:
        conn.close()
        flash("Match introuvable.")
        return redirect(url_for("matching.matches"))

    c.execute("UPDATE matches SET status='rejected' WHERE id=?", (match_id,))
    conn.commit()
    conn.close()

    flash("Match rejeté.")
    return redirect(url_for("matching.matches"))
