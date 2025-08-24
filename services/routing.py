import os
import requests
from typing import Dict, Any

OPENROUTESERVICE_API_KEY = os.environ.get("OPENROUTESERVICE_API_KEY", "")

COST_PER_KM_BY_MODE = {
    "driving-car": 0.25,     # USD per km (fuel/maintenance)
    "driving-hgv": 0.35,
    "cycling-regular": 0.0,
    "foot-walking": 0.0,
}
TIME_VALUE_PER_HOUR = 12.0  # USD/hour


def route_and_cost(start_lat: float, start_lon: float, end_lat: float, end_lon: float, mode: str) -> Dict[str, Any]:
    distance_km = None
    duration_min = None
    geometry = None

    if OPENROUTESERVICE_API_KEY:
        try:
            url = f"https://api.openrouteservice.org/v2/directions/{mode}"
            params = {
                "api_key": OPENROUTESERVICE_API_KEY,
                "start": f"{start_lon},{start_lat}",
                "end": f"{end_lon},{end_lat}",
                "geometry_format": "geojson",
            }
            r = requests.get(url, params=params, timeout=25)
            r.raise_for_status()
            data = r.json()
            feat = (data.get("features") or [{}])[0]
            props = feat.get("properties", {})
            summary = props.get("summary", {})
            distance_km = round((summary.get("distance", 0) or 0) / 1000.0, 2)
            duration_min = round((summary.get("duration", 0) or 0) / 60.0, 1)
            geometry = feat.get("geometry")
        except Exception:
            pass

    if distance_km is None or duration_min is None:
        # Fallback to OSRM (driving only)
        try:
            url = f"https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
            r = requests.get(url, params={"overview": "full", "geometries": "geojson"}, timeout=20)
            r.raise_for_status()
            data = r.json()
            route = (data.get("routes") or [{}])[0]
            distance_km = round((route.get("distance", 0) or 0) / 1000.0, 2)
            duration_min = round((route.get("duration", 0) or 0) / 60.0, 1)
            geometry = route.get("geometry")
            if mode != "driving-car":
                mode = "driving-car"
        except Exception:
            distance_km = 0.0
            duration_min = 0.0
            geometry = None

    # Cost model
    cost_per_km = COST_PER_KM_BY_MODE.get(mode, 0.25)
    fuel_cost = round(distance_km * cost_per_km, 2)
    time_cost = round((duration_min / 60.0) * TIME_VALUE_PER_HOUR, 2)
    total_cost = round(fuel_cost + time_cost, 2)

    return {
        "distance_km": distance_km,
        "duration_min": duration_min,
        "cost_usd": total_cost,
        "cost_breakdown": {"fuel": fuel_cost, "time": time_cost},
        "mode": mode,
        "geometry": geometry,
    }