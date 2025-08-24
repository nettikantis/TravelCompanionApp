import requests
from typing import Dict


def get_rates(base: str, symbols: str) -> Dict:
    base = (base or "USD").upper()
    symbols = (symbols or "EUR,GBP,CAD").upper()
    try:
        r = requests.get(
            "https://api.exchangerate.host/latest",
            params={"base": base, "symbols": symbols},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        return {"base": data.get("base", base), "rates": data.get("rates", {}), "symbols": symbols.split(",")}
    except Exception:
        return {"base": base, "rates": {}, "symbols": symbols.split(",")}