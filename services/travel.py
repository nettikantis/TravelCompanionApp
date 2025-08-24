from typing import Any, Dict, Optional

import requests


PROFILE_MAP = {
    "driving": "driving-car",
    "driving-car": "driving-car",
    "walking": "foot-walking",
    "foot": "foot-walking",
    "cycling": "cycling-regular",
}


def route_and_cost(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    mode: str,
    ors_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute route information using OpenRouteService when available; otherwise fallback to OSRM.
    Returns distance (km), duration (minutes), and a simple cost estimation per mode.
    """
    profile = PROFILE_MAP.get(mode, "driving-car")

    distance_km = 0.0
    duration_min = 0.0
    geometry = None

    if ors_api_key:
        url = f"https://api.openrouteservice.org/v2/directions/{profile}"
        headers = {"Authorization": ors_api_key, "Accept": "application/json"}
        payload = {"coordinates": [[origin_lon, origin_lat], [dest_lon, dest_lat]]}
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        summary = data["features"][0]["properties"]["summary"]
        distance_km = summary["distance"] / 1000.0
        duration_min = summary["duration"] / 60.0
        geometry = data["features"][0].get("geometry")
    else:
        # OSRM fallback (driving only). Other modes will approximate with driving route distance.
        osrm_profile = "car"
        url = (
            f"https://router.project-osrm.org/route/v1/{osrm_profile}/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
            f"?overview=full&geometries=geojson"
        )
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        route = data["routes"][0]
        distance_km = route["distance"] / 1000.0
        duration_min = route["duration"] / 60.0
        geometry = route.get("geometry")

    cost = estimate_cost(distance_km, mode)
    return {
        "distance_km": round(distance_km, 2),
        "duration_min": round(duration_min, 1),
        "mode": mode,
        "cost": cost,
        "geometry": geometry,
    }


def estimate_cost(distance_km: float, mode: str) -> Dict[str, float]:
    """Simple cost model for different modes (in USD)."""
    mode_key = mode.lower()
    if mode_key in ("driving", "driving-car"):
        # Fuel + wear/tear
        variable_cost_per_km = 0.5
        base_fee = 0.0
    elif mode_key in ("taxi",):
        variable_cost_per_km = 1.2
        base_fee = 1.5
    elif mode_key in ("cycling", "cycling-regular"):
        variable_cost_per_km = 0.02
        base_fee = 0.0
    elif mode_key in ("walking", "foot", "foot-walking"):
        variable_cost_per_km = 0.0
        base_fee = 0.0
    else:
        variable_cost_per_km = 0.4
        base_fee = 0.0

    total = base_fee + variable_cost_per_km * distance_km
    return {
        "base_fee_usd": round(base_fee, 2),
        "variable_usd": round(variable_cost_per_km * distance_km, 2),
        "total_usd": round(total, 2),
    }

