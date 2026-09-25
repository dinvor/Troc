import sqlite3
from flask import Flask, render_template, session
from flask_socketio import SocketIO, join_room, emit

# ---------------- SOCKET.IO ----------------

socketio = SocketIO(cors_allowed_origins="*", async_mode="gevent")


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


# ---------------- APP FACTORY ----------------

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret-key"

    # ---- Blueprints ----
    from auth.routes import auth_bp
    from products.routes import products_bp
    from matching.routes import matching_bp
    from chat.routes import chat_bp
    from api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(matching_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(api_bp)

    # ---- Inject user globally ----
    @app.context_processor
    def inject_user():
        return {"user": current_user()}

    # ---- Page d'accueil ----
    @app.route("/")
    def index():
        return render_template("products.html", products=[], user=current_user())

    socketio.init_app(app)
    return app


app = create_app()


# ---------------- SOCKET.IO EVENTS ----------------

@socketio.on("join")
def handle_join(data):
    room = data.get("room")
    if room:
        join_room(room)


@socketio.on("message")
def handle_message(data):
    room = data.get("room")
    sender_id = data.get("sender")
    content = data.get("content")

    if not room or not sender_id or not content:
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE id=?", (sender_id,))
    u = c.fetchone()
    sender_name = u["name"] if u else "Inconnu"

    c.execute("""
        INSERT INTO messages (match_id, sender_id, content)
        VALUES (?, ?, ?)
    """, (room, sender_id, content))
    conn.commit()
    conn.close()

    emit("message", {
        "sender_id": sender_id,
        "sender_name": sender_name,
        "content": content
    }, room=room)


# ---------------- MAIN ----------------

if __name__ == "__main__":
    socketio.run(app, debug=True, host="127.0.0.1", port=5000)
