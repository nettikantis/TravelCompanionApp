import os
import math
from flask import Blueprint, request, jsonify
import requests
from app import db
from models import Bookmark

api_bp = Blueprint("api", __name__)


# Helpers
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
ORS_API_KEY = os.getenv("ORS_API_KEY", "")
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "")


@api_bp.route("/search")
def search_city():
    city = request.args.get("city", type=str)
    if not city:
        return jsonify({"error": "Missing city parameter"}), 400

    # OpenWeather Geocoding API
    try:
        geo_url = "https://api.openweathermap.org/geo/1.0/direct"
        r = requests.get(geo_url, params={"q": city, "limit": 1, "appid": OPENWEATHER_API_KEY}, timeout=15)
        r.raise_for_status()
        results = r.json()
        if not results:
            return jsonify({"error": "City not found"}), 404
        item = results[0]
        resp = {
            "name": item.get("name"),
            "country": item.get("country"),
            "lat": item.get("lat"),
            "lon": item.get("lon"),
        }
        return jsonify(resp)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/places")
def get_places():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    category = request.args.get("category", default="attractions", type=str)
    if lat is None or lon is None:
        return jsonify({"error": "Missing lat/lon"}), 400

    categories_map = {
        "attractions": "16000",  # Landmarks and outdoors
        "parks": "16032",        # Parks
        "restaurants": "13065",  # Restaurants
        "cafes": "13032",
    }
    headers = {"Authorization": FOURSQUARE_API_KEY}
    params = {
        "ll": f"{lat},{lon}",
        "limit": 20,
        "sort": "DISTANCE",
    }
    # Prefer category id if known, else use query
    if category in categories_map:
        params["categories"] = categories_map[category]
    else:
        params["query"] = category

    try:
        url = "https://api.foursquare.com/v3/places/search"
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        places = []
        for p in data.get("results", []):
            geo = p.get("geocodes", {}).get("main", {})
            category_name = None
            cats = p.get("categories") or []
            if cats:
                category_name = cats[0].get("name")
            places.append({
                "id": p.get("fsq_id"),
                "name": p.get("name"),
                "category": category_name,
                "lat": geo.get("latitude"),
                "lon": geo.get("longitude"),
                "address": (p.get("location", {}).get("formatted_address")),
                "distance": p.get("distance"),
            })
        return jsonify({"places": places})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/weather")
def get_weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if lat is None or lon is None:
        return jsonify({"error": "Missing lat/lon"}), 400

    try:
        # Current weather
        current_url = "https://api.openweathermap.org/data/2.5/weather"
        current_resp = requests.get(
            current_url,
            params={"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            timeout=15,
        )
        current_resp.raise_for_status()
        current = current_resp.json()

        # 5-day forecast (3-hourly)
        forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
        forecast_resp = requests.get(
            forecast_url,
            params={"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            timeout=15,
        )
        forecast_resp.raise_for_status()
        forecast = forecast_resp.json()

        return jsonify({"current": current, "forecast": forecast})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/travel")
def get_travel():
    start_lat = request.args.get("start_lat", type=float)
    start_lon = request.args.get("start_lon", type=float)
    end_lat = request.args.get("end_lat", type=float)
    end_lon = request.args.get("end_lon", type=float)
    mode = request.args.get("mode", default="driving-car", type=str)

    if None in [start_lat, start_lon, end_lat, end_lon]:
        return jsonify({"error": "Missing coordinates"}), 400

    # OpenRouteService directions
    try:
        url = f"https://api.openrouteservice.org/v2/directions/{mode}"
        params = {
            "api_key": ORS_API_KEY,
            "start": f"{start_lon},{start_lat}",
            "end": f"{end_lon},{end_lat}",
            "geometry_format": "geojson",
        }
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        feat = data.get("features", [{}])[0]
        props = feat.get("properties", {})
        summary = props.get("summary", {})
        distance_m = summary.get("distance", 0)
        duration_s = summary.get("duration", 0)
        distance_km = round(distance_m / 1000.0, 2)
        duration_min = round(duration_s / 60.0, 1)

        # Simple cost model
        cost_per_km = {
            "driving-car": 0.5,
            "driving-hgv": 0.7,
            "cycling-regular": 0.0,
            "foot-walking": 0.0,
        }.get(mode, 0.5)
        fuel_cost = round(distance_km * cost_per_km, 2)
        time_cost = round((duration_s / 3600.0) * 15.0, 2)  # $15/hour value of time
        total_cost = round(fuel_cost + time_cost, 2)

        geometry = feat.get("geometry")

        return jsonify({
            "distance_km": distance_km,
            "duration_min": duration_min,
            "cost_usd": total_cost,
            "cost_breakdown": {"fuel": fuel_cost, "time": time_cost},
            "mode": mode,
            "geometry": geometry,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/rates")
def get_rates():
    base = request.args.get("base", default="USD", type=str)
    if not EXCHANGE_RATE_API_KEY:
        return jsonify({"error": "Rates API key not configured"}), 400
    try:
        url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/{base}"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Bookmarks endpoints
@api_bp.route("/bookmarks", methods=["GET"])
def list_bookmarks():
    items = Bookmark.query.order_by(Bookmark.created_at.desc()).all()
    return jsonify({"bookmarks": [b.to_dict() for b in items]})


@api_bp.route("/bookmarks", methods=["POST"])
def add_bookmark():
    data = request.get_json(force=True, silent=True) or {}
    required = ["city", "name", "lat", "lon"]
    if any(k not in data for k in required):
        return jsonify({"error": f"Missing fields: {', '.join(required)}"}), 400

    b = Bookmark(
        city=data.get("city"),
        name=data.get("name"),
        category=data.get("category"),
        lat=float(data.get("lat")),
        lon=float(data.get("lon")),
        external_id=data.get("external_id"),
    )
    db.session.add(b)
    db.session.commit()
    return jsonify(b.to_dict()), 201


@api_bp.route("/bookmarks/<int:bookmark_id>", methods=["DELETE"])
def delete_bookmark(bookmark_id: int):
    b = Bookmark.query.get_or_404(bookmark_id)
    db.session.delete(b)
    db.session.commit()
    return jsonify({"status": "deleted"})