# Smart Travel Companion Dashboard

Python/Flask web app to explore cities with place recommendations, weather, routing cost estimates, currency rates, bookmarks, charts, and an interactive map.

## Features
- Nearby place recommendations (Foursquare if key provided, else OpenStreetMap Overpass)
- Current weather + 5-day forecast (OpenWeatherMap)
- Travel distance, time, and cost (OpenRouteService if key provided, else OSRM)
- Currency rates (exchangerate.host)
- Leaflet map, Chart.js charts, Bootstrap UI
- Bookmarks via SQLite

## Project Structure
- `app.py`: Flask app factory and bootstrap
- `extensions.py`: Initializes shared extensions (`db`)
- `models.py`: SQLAlchemy models (Bookmark)
- `routes/`: Blueprints
  - `main.py`: Renders main dashboard
  - `api.py`: API endpoints (geocode, places, weather, travel, currency, bookmarks)
- `services/`: External API wrappers
  - `geocode.py`, `places.py`, `weather.py`, `travel.py`, `currency.py`
- `templates/`: `base.html`, `index.html`
- `static/`: `css/styles.css`, `js/app.js`

## Prerequisites
- Python 3.9+
- Free API keys (recommended):
  - FOURSQUARE_API_KEY — optional, improves place results
  - OPENWEATHERMAP_API_KEY — required for weather
  - OPENROUTESERVICE_API_KEY — optional; OSRM used if not provided

## Setup
1. Create and populate `.env` from `.env.example`:
```bash
cp .env.example .env
# Edit .env and set at least OPENWEATHERMAP_API_KEY
```
2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Locally
```bash
python app.py
```
Then open `http://localhost:5000`.

## Notes on Free APIs
- Geocoding uses OpenStreetMap Nominatim (no key). Consider setting `NOMINATIM_EMAIL` in env.
- Places uses Foursquare when `FOURSQUARE_API_KEY` exists; otherwise uses Overpass (OSM).
- Travel uses OpenRouteService when `OPENROUTESERVICE_API_KEY` exists; otherwise OSRM.
- Currency uses exchangerate.host (no key).

## Deploy
```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```