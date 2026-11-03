
from flask import Flask
from app.routes import search_bp
from flask_cors import CORS

def create_app():

    app = Flask(__name__)
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5500",
                    "http://127.0.0.1:5500"
                ]
            }
        }
    )    

    app.register_blueprint(search_bp)

    @app.route("/")
    def home():
        return {
            "success": True,
            "message": "Government Scheme Discovery System API is running."
        }

    return app
