import os
import requests
from typing import Dict, Any

OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY", "")
DEFAULT_UNITS = os.environ.get("DEFAULT_UNITS", "metric")


def get_weather(lat: float, lon: float, units: str = None) -> Dict[str, Any]:
    units = units or DEFAULT_UNITS
    if OPENWEATHERMAP_API_KEY:
        try:
            current_url = "https://api.openweathermap.org/data/2.5/weather"
            forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
            cur = requests.get(
                current_url,
                params={"lat": lat, "lon": lon, "appid": OPENWEATHERMAP_API_KEY, "units": units},
                timeout=15,
            )
            cur.raise_for_status()
            fr = requests.get(
                forecast_url,
                params={"lat": lat, "lon": lon, "appid": OPENWEATHERMAP_API_KEY, "units": units},
                timeout=15,
            )
            fr.raise_for_status()
            return {"provider": "owm", "current": cur.json(), "forecast": fr.json()}
        except Exception:
            pass

    # Fallback: Open-Meteo (free, no key)
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "temperature_2m",
            "timezone": "auto",
        }
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        # Normalize to OWM-like structure
        current_temp = data.get("current_weather", {}).get("temperature")
        current = {
            "main": {"temp": current_temp},
            "weather": [{"description": "current weather"}],
        }
        # Build a pseudo 5-day forecast every 6 hours from hourly temps
        times = data.get("hourly", {}).get("time", [])
        temps = data.get("hourly", {}).get("temperature_2m", [])
        list_items = []
        for i in range(0, min(len(times), len(temps)), 6):
            list_items.append({
                "dt_txt": times[i].replace("T", " "),
                "main": {"temp": temps[i]},
            })
        forecast = {"list": list_items[:40]}
        return {"provider": "open-meteo", "current": current, "forecast": forecast}
    except Exception:
        return {"provider": "none", "current": {}, "forecast": {"list": []}}