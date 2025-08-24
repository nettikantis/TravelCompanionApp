/* global L, Chart */

const state = {
  center: null,
  selectedPlace: null,
  markers: [],
  weatherChart: null,
  costChart: null,
};

const map = L.map('map');
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

function setMapCenter(lat, lon, zoom = 12) {
  state.center = { lat, lon };
  map.setView([lat, lon], zoom);
}

function fitToMarkers() {
  const group = new L.featureGroup(state.markers);
  try { map.fitBounds(group.getBounds().pad(0.2)); } catch (e) {}
}

async function geocode(q) {
  const r = await fetch(`/api/geocode?q=${encodeURIComponent(q)}`);
  const data = await r.json();
  return data.results?.[0] || null;
}

async function loadWeather(lat, lon, label) {
  const elCurrent = document.getElementById('current-weather');
  const elLoc = document.getElementById('weather-location');
  elLoc.textContent = label || '';
  try {
    const r = await fetch(`/api/weather?lat=${lat}&lon=${lon}`);
    const data = await r.json();
    if (data.error) throw new Error(data.error);
    const c = data.current;
    elCurrent.innerHTML = `
      <div class="d-flex align-items-center gap-3">
        <img src="https://openweathermap.org/img/wn/${c.weather?.[0]?.icon || '01d'}@2x.png" alt="icon" />
        <div>
          <div class="fs-4">${Math.round(c.main.temp)}°C, ${c.weather?.[0]?.main || ''}</div>
          <div class="text-muted small">Humidity ${c.main.humidity}% • Wind ${c.wind.speed} m/s</div>
        </div>
      </div>`;

    renderWeatherChart(data.daily);
  } catch (err) {
    elCurrent.innerHTML = `<div class="text-danger small">Weather unavailable: ${err.message}</div>`;
  }
}

function renderWeatherChart(daily) {
  const ctx = document.getElementById('weather-chart');
  if (state.weatherChart) state.weatherChart.destroy();
  state.weatherChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: daily.labels,
      datasets: [
        { label: 'Temp (°C)', data: daily.temp, borderColor: '#0d6efd', backgroundColor: 'rgba(13,110,253,0.15)', fill: true },
        { label: 'Wind (m/s)', data: daily.wind, borderColor: '#20c997', backgroundColor: 'rgba(32,201,151,0.1)', fill: true },
        { label: 'Humidity (%)', data: daily.humidity, borderColor: '#fd7e14', backgroundColor: 'rgba(253,126,20,0.1)', fill: true },
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom' } }
    }
  });
}

async function loadPlaces(lat, lon, query) {
  const grid = document.getElementById('places-grid');
  grid.innerHTML = '<div class="text-muted">Loading places…</div>';
  try {
    const preferFsq = document.getElementById('toggle-foursquare').checked;
    const src = preferFsq ? 'auto' : 'osm';
    const r = await fetch(`/api/places?lat=${lat}&lon=${lon}&query=${encodeURIComponent(query || '')}&source=${src}`);
    const data = await r.json();
    const items = data.results || [];
    document.getElementById('places-count').textContent = `${items.length} results`;

    // Clear markers
    state.markers.forEach(m => map.removeLayer(m));
    state.markers = [];

    grid.innerHTML = '';
    items.forEach(item => {
      const col = document.createElement('div');
      col.className = 'col-12 col-md-6 col-lg-4';
      col.innerHTML = `
        <div class="card place-card h-100" data-lat="${item.latitude}" data-lon="${item.longitude}" data-name="${item.name}" data-address="${item.address || ''}">
          <div class="card-body">
            <div class="d-flex align-items-start justify-content-between">
              <div>
                <div class="fw-semibold">${item.name}</div>
                <div class="text-muted small">${item.address || ''}</div>
              </div>
              <span class="badge rounded-pill text-bg-light badge-source">${item.source}</span>
            </div>
            <div class="small mt-2 text-muted">${item.categories || ''}</div>
            <div class="mt-3 d-flex gap-2">
              <button class="btn btn-sm btn-outline-primary btn-center">Center</button>
              <button class="btn btn-sm btn-outline-success btn-dest">Use as Destination</button>
              <button class="btn btn-sm btn-outline-secondary btn-bookmark">Bookmark</button>
            </div>
          </div>
        </div>`;
      grid.appendChild(col);

      const marker = L.marker([item.latitude, item.longitude]).addTo(map).bindPopup(`<strong>${item.name}</strong><br/>${item.address || ''}`);
      state.markers.push(marker);
    });

    fitToMarkers();

    grid.querySelectorAll('.btn-center').forEach(btn => btn.addEventListener('click', (e) => {
      const card = e.target.closest('.place-card');
      setMapCenter(parseFloat(card.dataset.lat), parseFloat(card.dataset.lon));
    }));
    grid.querySelectorAll('.btn-dest').forEach(btn => btn.addEventListener('click', (e) => {
      const card = e.target.closest('.place-card');
      state.selectedPlace = {
        name: card.dataset.name,
        address: card.dataset.address,
        latitude: parseFloat(card.dataset.lat),
        longitude: parseFloat(card.dataset.lon),
      };
      document.getElementById('dest-name').value = state.selectedPlace.name;
    }));
    grid.querySelectorAll('.btn-bookmark').forEach(btn => btn.addEventListener('click', async (e) => {
      const card = e.target.closest('.place-card');
      const payload = {
        name: card.dataset.name,
        address: card.dataset.address,
        latitude: parseFloat(card.dataset.lat),
        longitude: parseFloat(card.dataset.lon)
      };
      const resp = await fetch('/api/bookmarks', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (resp.ok) loadBookmarks();
    }));
  } catch (err) {
    grid.innerHTML = `<div class="text-danger">Failed to load places: ${err.message}</div>`;
  }
}

async function loadBookmarks() {
  const list = document.getElementById('bookmarks-list');
  list.innerHTML = '<div class="text-muted">Loading…</div>';
  const r = await fetch('/api/bookmarks');
  const data = await r.json();
  list.innerHTML = '';
  (data.results || []).forEach(b => {
    const a = document.createElement('a');
    a.href = '#';
    a.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
    a.innerHTML = `<span>${b.name}</span><button class="btn btn-sm btn-outline-danger">Delete</button>`;
    a.querySelector('button').addEventListener('click', async (e) => {
      e.preventDefault();
      await fetch(`/api/bookmarks/${b.id}`, { method: 'DELETE' });
      loadBookmarks();
    });
    a.addEventListener('click', (e) => {
      e.preventDefault();
      setMapCenter(b.latitude, b.longitude, 14);
    });
    list.appendChild(a);
  });
}

function renderCostChart(cost) {
  const ctx = document.getElementById('cost-chart');
  if (state.costChart) state.costChart.destroy();
  state.costChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Base Fee', 'Variable'],
      datasets: [{
        label: 'USD',
        data: [cost.base_fee_usd, cost.variable_usd],
        backgroundColor: ['#6f42c1', '#0dcaf0']
      }]
    },
    options: { plugins: { legend: { display: false } } }
  });
}

async function initFromQuery() {
  const inp = document.getElementById('location-input');
  const q = inp.value.trim();
  if (!q) return;
  const loc = await geocode(q);
  if (!loc) return;
  setMapCenter(parseFloat(loc.lat), parseFloat(loc.lon));
  await Promise.all([
    loadWeather(loc.lat, loc.lon, loc.display_name),
    loadPlaces(loc.lat, loc.lon, document.getElementById('query-type').value)
  ]);
}

document.getElementById('search-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  await initFromQuery();
});

document.getElementById('use-my-location').addEventListener('click', async () => {
  if (!navigator.geolocation) return alert('Geolocation not supported');
  navigator.geolocation.getCurrentPosition(async (pos) => {
    const { latitude, longitude } = pos.coords;
    setMapCenter(latitude, longitude);
    await Promise.all([
      loadWeather(latitude, longitude, 'Your location'),
      loadPlaces(latitude, longitude, document.getElementById('query-type').value)
    ]);
  }, (err) => alert('Failed to get location: ' + err.message));
});

document.getElementById('refresh-bookmarks').addEventListener('click', loadBookmarks);

document.getElementById('travel-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!state.center || !state.selectedPlace) return alert('Pick a destination from places');
  const mode = document.getElementById('travel-mode').value;
  const params = new URLSearchParams({
    origin_lat: state.center.lat,
    origin_lon: state.center.lon,
    dest_lat: state.selectedPlace.latitude,
    dest_lon: state.selectedPlace.longitude,
    mode
  });
  const r = await fetch(`/api/travel?${params.toString()}`);
  const data = await r.json();
  if (data.error) return alert(data.error);
  renderCostChart(data.cost);
  document.getElementById('travel-stats').textContent = `Distance ${data.distance_km} km • Duration ${data.duration_min} min`;

  // Draw route if geometry is present
  try {
    if (state.routeLayer) map.removeLayer(state.routeLayer);
  } catch (e) {}
  if (data.geometry && data.geometry.coordinates) {
    const coords = data.geometry.coordinates.map(c => [c[1], c[0]]);
    state.routeLayer = L.polyline(coords, { color: '#0d6efd' }).addTo(map);
    map.fitBounds(state.routeLayer.getBounds().pad(0.2));
  }
});

// Initialize page defaults
setMapCenter(40.7128, -74.0060, 11); // Default to New York
loadBookmarks();
if (document.getElementById('location-input').value) {
  initFromQuery();
}

