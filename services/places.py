import os
import requests
from typing import List, Dict

FOURSQUARE_API_KEY = os.environ.get("FOURSQUARE_API_KEY", "")


FSQ_CATEGORIES = {
    "restaurants": "13065",
    "cafes": "13032",
    "parks": "16032",
    "attractions": "16000",  # Landmarks & Outdoors
}


def _normalize_place(item) -> Dict:
    geo = (item.get("geocodes") or {}).get("main") or {}
    location = item.get("location") or {}
    categories = item.get("categories") or []
    cat = categories[0]["name"] if categories else None
    return {
        "name": item.get("name"),
        "category": cat,
        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),
        "address": location.get("formatted_address"),
        "city": location.get("locality"),
        "country": location.get("country"),
    }


def search_places(lat: float, lon: float, category: str, limit: int = 20) -> List[Dict]:
    if FOURSQUARE_API_KEY:
        try:
            url = "https://api.foursquare.com/v3/places/search"
            headers = {"Authorization": FOURSQUARE_API_KEY}
            params = {
                "ll": f"{lat},{lon}",
                "limit": limit,
                "sort": "DISTANCE",
            }
            if category in FSQ_CATEGORIES:
                params["categories"] = FSQ_CATEGORIES[category]
            else:
                params["query"] = category
            r = requests.get(url, headers=headers, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            return [_normalize_place(p) for p in data.get("results", [])]
        except Exception:
            pass

    # Fallback: Overpass API
    tag_filters = {
        "restaurants": "amenity=restaurant",
        "cafes": "amenity=cafe",
        "parks": "leisure=park",
        "attractions": "tourism=attraction",
    }
    tag = tag_filters.get(category, "tourism=attraction")
    radius = 2500
    overpass_query = f"""
    [out:json][timeout:25];
    (
      node(around:{radius},{lat},{lon})[{tag}];
      way(around:{radius},{lat},{lon})[{tag}];
      relation(around:{radius},{lat},{lon})[{tag}];
    );
    out center {limit};
    """
    try:
        r = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": overpass_query},
            headers={"User-Agent": "SmartTravelCompanion/1.0"},
            timeout=25,
        )
        r.raise_for_status()
        data = r.json()
        results = []
        for el in data.get("elements", [])[:limit]:
            tags = el.get("tags", {})
            name = tags.get("name") or tags.get("ref") or category.title()
            lat_out = el.get("lat") or (el.get("center") or {}).get("lat")
            lon_out = el.get("lon") or (el.get("center") or {}).get("lon")
            if lat_out is None or lon_out is None:
                continue
            address_parts = [
                tags.get("addr:street"),
                tags.get("addr:housenumber"),
                tags.get("addr:city"),
            ]
            address = ", ".join([p for p in address_parts if p])
            results.append(
                {
                    "name": name,
                    "category": category.title(),
                    "latitude": lat_out,
                    "longitude": lon_out,
                    "address": address,
                    "city": tags.get("addr:city"),
                    "country": tags.get("addr:country"),
                }
            )
        return results
    except Exception:
        return []