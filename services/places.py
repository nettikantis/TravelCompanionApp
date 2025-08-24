from typing import Any, Dict, List, Optional

import requests


def search_places(
    latitude: float,
    longitude: float,
    query: Optional[str] = None,
    api_key: Optional[str] = None,
    radius_meters: int = 5000,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Search nearby places using Foursquare Places API when api_key is provided.
    If api_key is None, gracefully fall back to OpenStreetMap Overpass API (free, unauthenticated).
    """
    if api_key:
        url = "https://api.foursquare.com/v3/places/search"
        headers = {
            "Authorization": api_key,
            "Accept": "application/json",
        }
        params = {
            "ll": f"{latitude},{longitude}",
            "radius": radius_meters,
            "limit": limit,
            "sort": "DISTANCE",
        }
        if query:
            params["query"] = query
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        items = resp.json().get("results", [])
        results: List[Dict[str, Any]] = []
        for x in items:
            geocodes = x.get("geocodes", {})
            main_geo = geocodes.get("main", {})
            loc = x.get("location", {})
            categories = ", ".join([c.get("name", "") for c in x.get("categories", []) if c.get("name")])
            results.append(
                {
                    "id": x.get("fsq_id"),
                    "name": x.get("name"),
                    "address": ", ".join(filter(None, [loc.get("address"), loc.get("locality"), loc.get("country")])),
                    "latitude": main_geo.get("latitude"),
                    "longitude": main_geo.get("longitude"),
                    "distance": x.get("distance"),
                    "categories": categories,
                    "source": "foursquare",
                }
            )
        return results

    # Fallback to Overpass API
    # Map simple query keywords to OSM tags
    osm_filters = {
        "restaurant": "amenity=restaurant",
        "park": "leisure=park",
        "attraction": "tourism=attraction",
        "cafe": "amenity=cafe",
        "bar": "amenity=bar",
        "museum": "tourism=museum",
    }
    tag = osm_filters.get((query or "").lower(), None)
    if tag is None:
        # Default to common POIs
        tag = "amenity=restaurant"

    # Build Overpass QL query
    # around:radius,lat,lon
    overpass_query = f"""
        [out:json][timeout:25];
        (
          node[{tag}](around:{radius_meters},{latitude},{longitude});
          way[{tag}](around:{radius_meters},{latitude},{longitude});
          relation[{tag}](around:{radius_meters},{latitude},{longitude});
        );
        out center {limit};
    """
    resp = requests.post("https://overpass-api.de/api/interpreter", data={"data": overpass_query}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for el in data.get("elements", [])[:limit]:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("brand") or (query or "Place")
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        address_parts = [tags.get("addr:street"), tags.get("addr:city"), tags.get("addr:country")]
        results.append(
            {
                "id": el.get("id"),
                "name": name,
                "address": ", ".join([p for p in address_parts if p]),
                "latitude": lat,
                "longitude": lon,
                "distance": None,
                "categories": query or tag,
                "source": "overpass",
            }
        )
    return results

