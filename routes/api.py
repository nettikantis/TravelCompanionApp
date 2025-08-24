from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request

from extensions import db
from models import Bookmark
from services.currency import fetch_rates
from services.geocode import geocode_location
from services.places import search_places
from services.travel import route_and_cost
from services.weather import fetch_current_and_forecast


api_bp = Blueprint("api", __name__)


@api_bp.route("/geocode")
def api_geocode():
    q = request.args.get("q")
    if not q:
        return jsonify({"error": "Missing 'q' parameter"}), 400
    results = geocode_location(q)
    return jsonify({"results": results})


@api_bp.route("/places")
def api_places():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    query = request.args.get("query")
    radius = request.args.get("radius", default=5000, type=int)
    source = request.args.get("source", default="auto")
    if lat is None or lon is None:
        return jsonify({"error": "Missing 'lat' or 'lon'"}), 400
    fsq_key = current_app.config.get("FOURSQUARE_API_KEY")
    # If source is explicitly 'osm', force fallback by passing None as api_key
    if source and source.lower() in ("osm", "overpass"):
        fsq_key = None
    results = search_places(lat, lon, query=query, api_key=fsq_key, radius_meters=radius)
    return jsonify({"results": results})


@api_bp.route("/weather")
def api_weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if lat is None or lon is None:
        return jsonify({"error": "Missing 'lat' or 'lon'"}), 400
    api_key = current_app.config.get("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return jsonify({"error": "Missing OpenWeatherMap API key"}), 500
    data = fetch_current_and_forecast(api_key, lat, lon)
    return jsonify(data)


@api_bp.route("/travel")
def api_travel():
    olat = request.args.get("origin_lat", type=float)
    olon = request.args.get("origin_lon", type=float)
    dlat = request.args.get("dest_lat", type=float)
    dlon = request.args.get("dest_lon", type=float)
    mode = request.args.get("mode", default="driving")
    if None in (olat, olon, dlat, dlon):
        return jsonify({"error": "Missing origin/destination coordinates"}), 400
    ors_key = current_app.config.get("OPENROUTESERVICE_API_KEY")
    data = route_and_cost(olat, olon, dlat, dlon, mode, ors_api_key=ors_key)
    return jsonify(data)


@api_bp.route("/currency")
def api_currency():
    base = request.args.get("base", default="USD")
    base_url = current_app.config.get("CURRENCY_API_BASE")
    rates = fetch_rates(base_url, base=base)
    return jsonify({"base": base, "rates": rates})


# --- Bookmarks endpoints ---


@api_bp.route("/bookmarks", methods=["GET"])
def list_bookmarks():
    items = Bookmark.query.order_by(Bookmark.created_at.desc()).all()
    return jsonify({"results": [b.to_dict() for b in items]})


@api_bp.route("/bookmarks", methods=["POST"])
def add_bookmark():
    payload: Dict[str, Any] = request.get_json(force=True)
    name = payload.get("name")
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    if not name or latitude is None or longitude is None:
        return jsonify({"error": "name, latitude, longitude are required"}), 400

    bookmark = Bookmark(
        name=name,
        address=payload.get("address"),
        city=payload.get("city"),
        latitude=float(latitude),
        longitude=float(longitude),
        note=payload.get("note"),
    )
    db.session.add(bookmark)
    db.session.commit()
    return jsonify(bookmark.to_dict()), 201


@api_bp.route("/bookmarks/<int:bookmark_id>", methods=["DELETE"])
def delete_bookmark(bookmark_id: int):
    bookmark = Bookmark.query.get_or_404(bookmark_id)
    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({"status": "deleted", "id": bookmark_id})

