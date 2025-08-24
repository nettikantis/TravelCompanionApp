import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///travel.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # External API Keys
    FOURSQUARE_API_KEY = os.environ.get("FOURSQUARE_API_KEY", "")
    OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY", "")
    OPENROUTESERVICE_API_KEY = os.environ.get("OPENROUTESERVICE_API_KEY", "")

    # Currency API key is optional; using free exchangerate.host by default
    EXCHANGE_RATE_API_KEY = os.environ.get("EXCHANGE_RATE_API_KEY", "")

    # UI Defaults
    DEFAULT_UNITS = os.environ.get("DEFAULT_UNITS", "metric")  # metric or imperial