# Smart Travel Companion Dashboard

A Flask-based web app that helps travelers explore cities with place recommendations, weather forecasts, travel cost estimation, currency rates, bookmarks, and an interactive map.

## Features
- Place recommendations via Foursquare Places API
- Current weather and 5-day forecast via OpenWeatherMap
- Travel distance, duration, and cost via OpenRouteService
- Optional currency rates via ExchangeRate-API
- Bookmarks stored in SQLite
- Leaflet map, Chart.js charts, Bootstrap UI

## Project Structure
- `app.py`: Flask app factory and bootstrap
- `models.py`: SQLAlchemy models (Bookmark)
- `routes/`: Blueprints for UI and API
  - `ui.py`: Renders main dashboard
  - `api.py`: Endpoints to call external services and manage bookmarks
- `templates/`: Jinja templates
  - `base.html`, `index.html`
- `static/`: Frontend assets
  - `css/styles.css`
  - `js/main.js`
- `instance/`: SQLite database lives here (`app.db`)

## Prerequisites
- Python 3.10+
- API Keys:
  - FOURSQUARE_API_KEY: https://location.foursquare.com/developer
  - OPENWEATHER_API_KEY: https://openweathermap.org/api
  - ORS_API_KEY: https://openrouteservice.org/dev/
  - EXCHANGE_RATE_API_KEY (optional): https://www.exchangerate-api.com/

## Setup
1. Clone/download this repo.
2. Create and populate `.env` from `.env.example`:
```
cp .env.example .env
# Edit .env and add your API keys
```
3. Create a virtual environment and install dependencies:
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Locally
```
python app.py
```
Then open `http://localhost:5000` in your browser.

## Usage Tips
- Search for a city (e.g., "Paris").
- Use place category buttons to load nearby attractions/parks/restaurants/cafes.
- Enter a destination city and pick a mode to estimate travel route and costs.
- Bookmark any place using the star button; manage bookmarks in the sidebar.

## Environment Variables
- `FLASK_SECRET_KEY`: Session secret
- `FOURSQUARE_API_KEY`: Foursquare Places API key
- `OPENWEATHER_API_KEY`: OpenWeatherMap key
- `ORS_API_KEY`: OpenRouteService key
- `EXCHANGE_RATE_API_KEY`: Exchange Rate API key (optional)
- `DATABASE_URL`: Optional DB URL, defaults to `sqlite:///instance/app.db`

## Notes
- This project uses public API endpoints. Ensure your keys and usage comply with provider terms.
- For production, disable debug mode and configure a production-ready server.