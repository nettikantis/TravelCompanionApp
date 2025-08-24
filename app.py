import os
from datetime import datetime

from flask import Flask
from dotenv import load_dotenv

from extensions import db


def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Core configuration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///travel.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Third-party APIs
    app.config["FOURSQUARE_API_KEY"] = os.getenv("FOURSQUARE_API_KEY")
    app.config["OPENWEATHERMAP_API_KEY"] = os.getenv("OPENWEATHERMAP_API_KEY")
    app.config["OPENROUTESERVICE_API_KEY"] = os.getenv("OPENROUTESERVICE_API_KEY")
    app.config["CURRENCY_API_BASE"] = os.getenv("CURRENCY_API_BASE", "https://api.exchangerate.host/latest")

    # Initialize extensions
    db.init_app(app)

    # Import models for table creation
    from models import Bookmark  # noqa: F401

    # Register blueprints
    from routes.main import main_bp
    from routes.api import api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Create tables
    with app.app_context():
        db.create_all()

    @app.get("/health")
    def health_check():
        return {"status": "ok", "time": datetime.utcnow().isoformat()}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)