let map;
let markersLayer;
let forecastChart;
let costChart;
let lastCoords = null;

function initMap() {
  map = L.map('map').setView([20, 0], 2);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
  markersLayer = L.layerGroup().addTo(map);
}

function setMapCenter(lat, lon) {
  map.setView([lat, lon], 12);
}

function addMarker(lat, lon, title) {
  const marker = L.marker([lat, lon]).addTo(markersLayer);
  if (title) marker.bindPopup(title);
  return marker;
}

function clearMarkers() {
  markersLayer.clearLayers();
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed ${res.status}`);
  return res.json();
}

function renderPlaces(places) {
  const grid = document.getElementById('places-grid');
  grid.innerHTML = '';
  document.getElementById('places-count').textContent = `${places.length} results`;
  clearMarkers();
  places.forEach(p => {
    const col = document.createElement('div');
    col.className = 'col-12 col-sm-6 col-lg-4';
    col.innerHTML = `
      <div class="card h-100 shadow-sm">
        <div class="card-body d-flex flex-column">
          <div class="d-flex align-items-start justify-content-between">
            <div>
              <h6 class="card-title mb-1">${p.name ?? 'Unknown'}</h6>
              <div class="text-muted small">${p.category ?? ''}</div>
            </div>
            <button class="btn btn-outline-primary btn-sm" title="Bookmark" onclick='saveBookmark(${JSON.stringify(JSON.stringify(p))})'><i class="fa fa-bookmark"></i></button>
          </div>
          <div class="mt-2 small text-muted">${p.address ?? ''}</div>
          <div class="mt-auto d-flex gap-2">
            <button class="btn btn-sm btn-outline-secondary" onclick="panTo(${p.latitude}, ${p.longitude})"><i class="fa fa-location-crosshairs"></i> View</button>
            <button class="btn btn-sm btn-outline-success" onclick="estimateRoute(${p.latitude}, ${p.longitude})"><i class="fa fa-route"></i> Route</button>
          </div>
        </div>
      </div>`;
    grid.appendChild(col);
    addMarker(p.latitude, p.longitude, p.name);
  });
}

function saveBookmark(serialized) {
  const p = JSON.parse(serialized);
  fetch('/api/bookmarks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: p.name || 'Place',
      latitude: p.latitude,
      longitude: p.longitude,
      city: p.city || '',
      country: p.country || '',
      notes: p.address || ''
    })
  }).then(() => refreshBookmarks());
}

function deleteBookmark(id) {
  fetch(`/api/bookmarks/${id}`, { method: 'DELETE' })
    .then(() => refreshBookmarks());
}

function refreshBookmarks() {
  fetch('/api/bookmarks')
    .then(r => r.json())
    .then(items => {
      const list = document.getElementById('bookmarks-list');
      if (!list) return;
      list.innerHTML = '';
      items.forEach(b => {
        const div = document.createElement('div');
        div.className = 'list-group-item d-flex justify-content-between align-items-center';
        div.innerHTML = `
          <div>
            <div class="fw-semibold">${b.name}</div>
            <div class="text-muted small">${b.city ?? ''} ${b.country ?? ''} (${b.latitude.toFixed(4)}, ${b.longitude.toFixed(4)})</div>
          </div>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteBookmark(${b.id})"><i class="fa fa-trash"></i></button>`;
        list.appendChild(div);
      });
    });
}

function renderWeather(current, forecastList, locationLabel) {
  document.getElementById('weather-location').textContent = locationLabel || '';
  const temp = current?.main?.temp;
  const desc = current?.weather?.[0]?.description;
  document.getElementById('current-weather').textContent = (temp !== undefined) ? `${Math.round(temp)}°` : '--';
  document.getElementById('current-description').textContent = desc ? desc : '';

  const labels = forecastList.map(i => i.dt_txt?.slice(5, 16) || '');
  const temps = forecastList.map(i => i.main?.temp ?? null);
  if (forecastChart) forecastChart.destroy();
  const ctx = document.getElementById('forecastChart').getContext('2d');
  forecastChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Temp',
        data: temps,
        borderColor: '#0d6efd',
        backgroundColor: 'rgba(13,110,253,0.2)',
        tension: 0.35,
        fill: true,
      }]
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: false } } }
  });
}

function renderCostChart(cost) {
  if (costChart) costChart.destroy();
  const ctx = document.getElementById('costChart').getContext('2d');
  costChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Fuel', 'Time'],
      datasets: [{
        data: [cost.cost_breakdown?.fuel ?? 0, cost.cost_breakdown?.time ?? 0],
        backgroundColor: ['#20c997', '#ffc107']
      }]
    },
    options: { plugins: { legend: { position: 'bottom' } } }
  });
}

function panTo(lat, lon) {
  setMapCenter(lat, lon);
}

async function estimateRoute(destLat, destLon) {
  if (!lastCoords) return;
  const mode = document.getElementById('mode-select').value;
  const url = `/api/route?start_lat=${lastCoords.lat}&start_lon=${lastCoords.lon}&end_lat=${destLat}&end_lon=${destLon}&mode=${encodeURIComponent(mode)}`;
  const data = await fetchJSON(url);
  if (data.distance_km != null) {
    document.getElementById('route-summary').textContent = `${data.distance_km} km • ${data.duration_min} min`;
    renderCostChart({ cost_breakdown: { fuel: data.cost_usd ? data.cost_usd * 0.7 : 0, time: data.cost_usd ? data.cost_usd * 0.3 : 0 } });
  }
}

async function onSearch() {
  const query = document.getElementById('search-input').value.trim();
  const category = document.getElementById('category-select').value;
  if (!query) return;

  const search = await fetchJSON(`/api/search?q=${encodeURIComponent(query)}`);
  const center = search?.center || search?.results?.[0]?.center;
  const label = search?.label || search?.results?.[0]?.label || query;
  if (center) {
    lastCoords = { lat: center.lat, lon: center.lon };
    setMapCenter(center.lat, center.lon);

    const w = await fetchJSON(`/api/weather?lat=${center.lat}&lon=${center.lon}`);
    renderWeather(w.current, w.forecast?.list || [], label);

    const placesRes = await fetchJSON(`/api/search?q=${encodeURIComponent(query)}&category=${encodeURIComponent(category)}`);
    const places = placesRes.places || placesRes.results || [];
    renderPlaces(places.map(p => ({
      name: p.name,
      category: p.category,
      latitude: p.latitude || p.lat,
      longitude: p.longitude || p.lon,
      address: p.address,
      city: p.city,
      country: p.country
    })).filter(p => p.latitude && p.longitude));
  }
}

window.addEventListener('DOMContentLoaded', () => {
  initMap();
  const btn = document.getElementById('search-btn');
  btn?.addEventListener('click', onSearch);
  document.getElementById('refresh-bookmarks')?.addEventListener('click', refreshBookmarks);
});