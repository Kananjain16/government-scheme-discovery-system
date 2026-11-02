
from flask import Flask
from app.routes import search_bp


def create_app():

    app = Flask(__name__)

    app.register_blueprint(search_bp)

    @app.route("/")
    def home():
        return {
            "success": True,
            "message": "Government Scheme Discovery System API is running."
        }

    return app
