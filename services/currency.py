from typing import Dict, Optional

import requests


def fetch_rates(base_url: str, base: str = "USD") -> Dict[str, float]:
    """
    Fetch currency rates using exchangerate.host (free, no API key). Compatible with ExchangeRate-API style.
    """
    params = {"base": base}
    resp = requests.get(base_url, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    rates = data.get("rates", {})
    return {k: float(v) for k, v in rates.items() if isinstance(v, (int, float))}

