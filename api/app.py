import os
import sys
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import psycopg

# Ensure sibling project modules are importable when running app.py directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from routes.ingredient_routes import ingredient_bp

# Load environment variables from the backend root .env file
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path)

# Get DATABASE_URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        f"DATABASE_URL no configurado. Asegúrate de que {dotenv_path} existe y contiene DATABASE_URL."
    )

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend", "foodsaver")
print('DEBUG startup ROOT_DIR', ROOT_DIR)
print('DEBUG startup FRONTEND_DIR', FRONTEND_DIR)

app = Flask(__name__)

# Enable CORS
CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=True
)

# Register routes
app.register_blueprint(ingredient_bp, url_prefix="/api/ingredients")


# -----------------------------
# DATABASE TEST
# -----------------------------
def test_db_connection():
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()

        print("✅ Database connected successfully")
        print(version)

    except Exception as e:
        print("❌ Database connection failed")
        print(e)


# -----------------------------
# FRONTEND ROUTES
# -----------------------------
@app.route("/")
def index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    print('DEBUG index_path', index_path, os.path.isfile(index_path))
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.before_request
def serve_frontend_assets():
    print('DEBUG before_request', request.path, request.method)
    if request.path.startswith("/api") or request.path.startswith("/__"):
        print('DEBUG before_request skipping api or internal route')
        return None

    if request.method != "GET":
        return None

    path = request.path.lstrip("/")
    if path == "":
        return send_from_directory(FRONTEND_DIR, "index.html")

    static_path = os.path.join(FRONTEND_DIR, path)
    print('DEBUG before_request static_path', path, static_path, os.path.isfile(static_path))
    if os.path.isfile(static_path):
        return send_from_directory(FRONTEND_DIR, path)

    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route('/__routes__')
def debug_routes():
    return jsonify([str(rule) for rule in app.url_map.iter_rules()])


# -----------------------------
# API HEALTH CHECK
# -----------------------------
@app.get("/api")
def health():
    return jsonify({
        "message": "API running",
        "database": "connected",
        "docs": "/api/ingredients"
    })


# -----------------------------
# TEST DATABASE ENDPOINT
# -----------------------------
@app.get("/api/test-db")
def test_db():
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT NOW();")
                result = cur.fetchone()

        return jsonify({
            "success": True,
            "timestamp": result[0]
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# -----------------------------
# ERROR HANDLER
# -----------------------------
from werkzeug.exceptions import HTTPException


@app.errorhandler(Exception)
def handle_error(error):
    status = getattr(error, 'code', None)
    if not isinstance(status, int):
        status = 500

    print('DEBUG error handler', type(error), status, str(error))
    return jsonify({
        "success": False,
        "error": str(error)
    }), status


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    print("📦 DATABASE_URL loaded:", bool(DATABASE_URL))

    test_db_connection()

    port = int(os.getenv("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
        use_reloader=False
    )