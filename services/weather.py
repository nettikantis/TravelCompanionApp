from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


def fetch_current_and_forecast(api_key: str, latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Fetch current weather and 5-day forecast (3h steps) from OpenWeatherMap.
    Returns a dict with 'current', 'forecast_raw', and 'daily' aggregated for charts.
    """
    if not api_key:
        raise ValueError("OpenWeatherMap API key is required")

    base = "https://api.openweathermap.org/data/2.5"
    params_common = {"lat": latitude, "lon": longitude, "appid": api_key, "units": "metric"}

    current = requests.get(f"{base}/weather", params=params_common, timeout=20).json()
    forecast = requests.get(f"{base}/forecast", params=params_common, timeout=20).json()

    # Aggregate to daily averages for chart
    by_day: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: {"temp": [], "wind": [], "humidity": []})
    for item in forecast.get("list", []):
        dt_txt = item.get("dt_txt")
        if not dt_txt:
            # fall back to unix timestamp if needed
            dt = datetime.utcfromtimestamp(item.get("dt", 0))
            day_key = dt.strftime("%Y-%m-%d")
        else:
            day_key = dt_txt.split(" ")[0]
        main = item.get("main", {})
        wind = item.get("wind", {})
        by_day[day_key]["temp"].append(main.get("temp"))
        by_day[day_key]["wind"].append(wind.get("speed"))
        by_day[day_key]["humidity"].append(main.get("humidity"))

    labels: List[str] = []
    temps: List[float] = []
    winds: List[float] = []
    hums: List[float] = []

    for day in sorted(by_day.keys())[:5]:
        labels.append(day)
        temps.append(_avg(by_day[day]["temp"]))
        winds.append(_avg(by_day[day]["wind"]))
        hums.append(_avg(by_day[day]["humidity"]))

    return {
        "current": current,
        "forecast_raw": forecast,
        "daily": {"labels": labels, "temp": temps, "wind": winds, "humidity": hums},
    }


def _avg(values: List[Optional[float]]) -> float:
    nums = [v for v in values if isinstance(v, (int, float))]
    return sum(nums) / len(nums) if nums else 0.0

