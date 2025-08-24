import os
from typing import Any, Dict, List, Optional

import requests


def geocode_location(query: str, email: Optional[str] = None, limit: int = 1) -> List[Dict[str, Any]]:
    """
    Geocode a free-form query using OpenStreetMap Nominatim (no API key required).
    Returns a list of results with latitude, longitude, display_name, and bounding box.
    """
    headers = {
        "User-Agent": f"SmartTravelDashboard/1.0 ({email or os.getenv('NOMINATIM_EMAIL','noreply@example.com')})"
    }
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": limit,
        "extratags": 0,
    }
    resp = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data:
        results.append(
            {
                "display_name": item.get("display_name"),
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "boundingbox": item.get("boundingbox"),
                "type": item.get("type"),
                "class": item.get("class"),
            }
        )
    return results

