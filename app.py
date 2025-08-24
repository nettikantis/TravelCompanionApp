import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Initialize extensions
load_dotenv()
db = SQLAlchemy()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Basic configuration
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

    # Database configuration
    default_sqlite_path = os.path.join(os.getcwd(), "instance", "app.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", f"sqlite:///{default_sqlite_path}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Ensure instance folder exists
    try:
        os.makedirs(os.path.join(os.getcwd(), "instance"), exist_ok=True)
    except OSError:
        pass

    # Initialize db
    db.init_app(app)

    # Import models so that SQLAlchemy is aware
    from models import Bookmark  # noqa: F401

    # Register blueprints
    from routes.ui import ui_bp
    from routes.api import api_bp

    app.register_blueprint(ui_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Create tables
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)