import os

from dotenv import load_dotenv
from flask import Flask, jsonify

from routes.ingredient_routes import ingredient_bp


load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)

    app.register_blueprint(ingredient_bp, url_prefix="/api/ingredients")

    @app.get("/")
    def health():
        return jsonify({"message": "API running", "docs": "/api/ingredients"})

    @app.errorhandler(Exception)
    def handle_error(error):
        status = getattr(error, "status_code", 500)
        message = str(error) if str(error) else "Internal server error"
        return jsonify({"error": message}), status

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "3000"))
    app.run(host="0.0.0.0", port=port)
