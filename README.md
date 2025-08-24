# Smart Travel Companion Dashboard

A Flask-based web app that helps travelers plan trips with place recommendations, weather forecasts, travel cost estimation, currency conversion, bookmarking, and an interactive map.

## Features
- Place recommendations via Foursquare (with OpenStreetMap Overpass fallback)
- Weather: OpenWeatherMap (with Open-Meteo fallback)
- Travel distance and cost: OpenRouteService (with OSRM fallback)
- Currency conversion: exchangerate.host (free)
- Bookmark favorite destinations (SQLite)
- Interactive map via Leaflet + OpenStreetMap
- Charts via Chart.js
- Responsive UI with Bootstrap 5

## Project Structure
```
app.py
config.py
models.py
routes/
  ├─ __init__.py
  ├─ main.py
  └─ api.py
services/
  ├─ __init__.py
  ├─ geocode.py
  ├─ places.py
  ├─ weather.py
  ├─ routing.py
  └─ currency.py
static/
  ├─ css/styles.css
  └─ js/main.js
templates/
  ├─ base.html
  └─ index.html
requirements.txt
README.md
.env.example
```

## Prerequisites
- Python 3.10+

## Setup
1. Clone or copy this repository into your workspace.
2. Create and edit an environment file:
   ```bash
   cp .env.example .env
   # edit .env to add keys (optional: app has free fallbacks)
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   flask --app app run --host 0.0.0.0 --port 5000 --debug
   # or: python app.py
   ```
5. Open in your browser: `http://localhost:5000`

## Environment Variables
- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: SQLAlchemy database URL (default SQLite file)
- `DEFAULT_UNITS`: `metric` or `imperial`
- `OPENWEATHERMAP_API_KEY`: Optional key. If not provided, app uses Open-Meteo for weather
- `FOURSQUARE_API_KEY`: Optional key for better place search; else uses Overpass
- `OPENROUTESERVICE_API_KEY`: Optional key for routing; else uses OSRM (driving only)
- `EXCHANGE_RATE_API_KEY`: Not required; using exchangerate.host

## Free APIs Used
- Geocoding: OpenWeatherMap Geocoding API (optional) or Nominatim (free)
- Places: Foursquare Places (optional) or Overpass API (free)
- Weather: OpenWeatherMap (optional) or Open-Meteo (free)
- Routing: OpenRouteService (optional) or OSRM (free driving)
- Currency: exchangerate.host (free)

## Notes
- Respect usage policies for public endpoints (set a descriptive User-Agent).
- If you provide API keys, you'll get higher-quality data/routes; otherwise free fallbacks keep the app fully usable.

## Bookmark Database
- SQLite file created automatically on first run.
- Endpoints:
  - `GET /api/bookmarks` list
  - `POST /api/bookmarks` create
  - `DELETE /api/bookmarks/<id>` delete

## Screenshots
- After start, search a city, choose a category, and click Search. Weather and places populate, map centers, and you can bookmark or estimate travel costs to a place.

## License
MIT