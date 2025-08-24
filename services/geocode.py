import os
import requests

OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY", "")


def geocode_city(query: str):
    query = query.strip()
    if not query:
        raise ValueError("Empty query")

    if OPENWEATHERMAP_API_KEY:
        try:
            url = "https://api.openweathermap.org/geo/1.0/direct"
            r = requests.get(
                url,
                params={"q": query, "limit": 1, "appid": OPENWEATHERMAP_API_KEY},
                timeout=15,
            )
            r.raise_for_status()
            items = r.json()
            if not items:
                return None
            item = items[0]
            city = item.get("name")
            country = item.get("country")
            return {
                "label": f"{city}, {country}" if city and country else query,
                "center": {"lat": item.get("lat"), "lon": item.get("lon")},
                "city": city,
                "country": country,
            }
        except Exception:
            pass

    # Fallback to Nominatim (free, no key)
    try:
        url = "https://nominatim.openstreetmap.org/search"
        r = requests.get(
            url,
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": "SmartTravelCompanion/1.0"},
            timeout=15,
        )
        r.raise_for_status()
        items = r.json()
        if not items:
            return None
        item = items[0]
        display = item.get("display_name")
        return {
            "label": display or query,
            "center": {"lat": float(item.get("lat")), "lon": float(item.get("lon"))},
            "city": None,
            "country": None,
        }
    except Exception:
        return None