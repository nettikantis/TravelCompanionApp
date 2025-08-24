import os
import math
from flask import Blueprint, jsonify, request
import requests
from app import db
from models import Bookmark

from services.geocode import geocode_city
from services.places import search_places
from services.weather import get_weather
from services.routing import route_and_cost
from services.currency import get_rates

api_bp = Blueprint("api", __name__)


# Helpers
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
ORS_API_KEY = os.getenv("ORS_API_KEY", "")
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "")


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@api_bp.route("/search", methods=["GET"])  # search city and optionally places
def search():
    query = request.args.get("q", "").strip()
    category = request.args.get("category")
    if not query:
        return jsonify({"error": "Missing query"}), 400

    geocode = geocode_city(query)
    if not geocode:
        return jsonify({"error": "Location not found"}), 404

    response = {"label": geocode["label"], "center": geocode["center"], "results": []}

    if category:
        lat = geocode["center"]["lat"]
        lon = geocode["center"]["lon"]
        places = search_places(lat, lon, category)
        response["places"] = places

    return jsonify(response)


@api_bp.route("/weather", methods=["GET"])  # weather for coordinates
def weather():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid or missing lat/lon"}), 400

    units = request.args.get("units")
    data = get_weather(lat, lon, units)
    return jsonify({"lat": lat, "lon": lon, "current": data.get("current", {}), "forecast": data.get("forecast", {})})


@api_bp.route("/route", methods=["GET"])  # distance and cost estimate
def route():
    try:
        start_lat = float(request.args.get("start_lat"))
        start_lon = float(request.args.get("start_lon"))
        end_lat = float(request.args.get("end_lat"))
        end_lon = float(request.args.get("end_lon"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid coordinates"}), 400

    mode = request.args.get("mode", "driving-car")
    result = route_and_cost(start_lat, start_lon, end_lat, end_lon, mode)
    return jsonify(result)


@api_bp.route("/currency", methods=["GET"])  # optional: currency conversion
def currency():
    base = request.args.get("base", "USD").upper()
    symbols = request.args.get("symbols", "EUR,GBP,CAD").upper()
    data = get_rates(base, symbols)
    return jsonify(data)


@api_bp.route("/bookmarks", methods=["GET", "POST"])  # list/create bookmarks
def bookmarks():
    from models import db, Bookmark

    if request.method == "POST":
        data = request.get_json(force=True)
        try:
            bookmark = Bookmark(
                name=data.get("name"),
                latitude=float(data.get("latitude")),
                longitude=float(data.get("longitude")),
                city=data.get("city"),
                country=data.get("country"),
                notes=data.get("notes"),
            )
            db.session.add(bookmark)
            db.session.commit()
            return jsonify(bookmark.to_dict()), 201
        except Exception as exc:
            db.session.rollback()
            return jsonify({"error": str(exc)}), 400

    # GET
    from models import Bookmark as B

    items = B.query.order_by(B.created_at.desc()).all()
    return jsonify([b.to_dict() for b in items])


@api_bp.route("/bookmarks/<int:bookmark_id>", methods=["DELETE"])  # delete
def delete_bookmark(bookmark_id: int):
    from models import db, Bookmark

    bookmark = Bookmark.query.get_or_404(bookmark_id)
    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({"deleted": bookmark_id})