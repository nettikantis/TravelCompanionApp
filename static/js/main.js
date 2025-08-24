let map, markerGroup, routeLayer;
let currentLocation = null; // {lat, lon, name}
let weatherChart, costChart;

function initMap() {
  map = L.map('mapContainer').setView([20, 0], 2);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
  markerGroup = L.layerGroup().addTo(map);
}

async function searchCity() {
  const city = document.getElementById('cityInput').value.trim();
  if (!city) return;
  setLoading(true);
  try {
    const res = await fetch(`/api/search?city=${encodeURIComponent(city)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Search failed');
    currentLocation = { lat: data.lat, lon: data.lon, name: `${data.name}, ${data.country}` };

    map.setView([data.lat, data.lon], 12);
    if (markerGroup) markerGroup.clearLayers();
    L.marker([data.lat, data.lon]).addTo(markerGroup).bindPopup(currentLocation.name).openPopup();

    await Promise.all([
      loadPlaces('attractions'),
      loadWeather(),
    ]);
  } catch (e) {
    alert(e.message);
  } finally {
    setLoading(false);
  }
}

async function loadPlaces(category) {
  if (!currentLocation) return;
  const url = `/api/places?lat=${currentLocation.lat}&lon=${currentLocation.lon}&category=${encodeURIComponent(category)}`;
  const res = await fetch(url);
  const data = await res.json();
  const container = document.getElementById('places');
  container.innerHTML = '';

  if (res.ok) {
    data.places.forEach(p => {
      const col = document.createElement('div');
      col.className = 'col';
      col.innerHTML = `
        <div class="card place-card">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h6 class="mb-1">${p.name || 'Unknown'}</h6>
                <div class="text-muted small">${p.category || ''}</div>
                <div class="text-muted small">${p.address || ''}</div>
              </div>
              <div class="text-end">
                <span class="badge text-bg-light badge-small">${Math.round((p.distance||0))} m</span>
                <button class="btn btn-sm btn-outline-primary mt-2" data-lat="${p.lat}" data-lon="${p.lon}" data-name="${encodeURIComponent(p.name)}" data-cat="${encodeURIComponent(p.category || '')}" data-id="${p.id}" onclick="bookmarkPlace(this)">★</button>
              </div>
            </div>
          </div>
        </div>`;
      container.appendChild(col);

      if (p.lat && p.lon) {
        L.marker([p.lat, p.lon]).addTo(markerGroup).bindPopup(p.name || 'Place');
      }
    });
  } else {
    container.innerHTML = `<div class="text-danger small">${data.error || 'Failed to load places'}</div>`;
  }
}

async function loadWeather() {
  const res = await fetch(`/api/weather?lat=${currentLocation.lat}&lon=${currentLocation.lon}`);
  const data = await res.json();
  if (!res.ok) {
    console.error(data);
    return;
  }
  const list = data.forecast.list;
  const labels = list.map(i => new Date(i.dt * 1000).toLocaleString());
  const temps = list.map(i => i.main.temp);

  if (weatherChart) weatherChart.destroy();
  const ctx = document.getElementById('weatherChart');
  weatherChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Temp (°C)',
        data: temps,
        borderColor: '#0d6efd',
        backgroundColor: 'rgba(13,110,253,0.1)',
        tension: 0.3,
      }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: false } }
    }
  });
}

async function estimateCost() {
  if (!currentLocation) return;
  const dest = document.getElementById('destInput').value.trim();
  if (!dest) return;

  setLoading(true);
  try {
    const destRes = await fetch(`/api/search?city=${encodeURIComponent(dest)}`);
    const destData = await destRes.json();
    if (!destRes.ok) throw new Error(destData.error || 'Destination not found');

    const mode = document.getElementById('modeSelect').value;
    const qs = `start_lat=${currentLocation.lat}&start_lon=${currentLocation.lon}&end_lat=${destData.lat}&end_lon=${destData.lon}&mode=${encodeURIComponent(mode)}`;
    const res = await fetch(`/api/travel?${qs}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Travel estimation failed');

    // Draw route
    if (routeLayer) routeLayer.remove();
    if (data.geometry) {
      routeLayer = L.geoJSON(data.geometry).addTo(map);
      map.fitBounds(routeLayer.getBounds(), { padding: [20, 20] });
    }

    // Update stats
    document.getElementById('routeStats').innerHTML = `
      <div class="alert alert-light">
        Distance: <strong>${data.distance_km} km</strong>, Duration: <strong>${data.duration_min} min</strong>, Cost: <strong>$${data.cost_usd}</strong>
      </div>`;

    // Cost chart
    if (costChart) costChart.destroy();
    const cctx = document.getElementById('costChart');
    costChart = new Chart(cctx, {
      type: 'doughnut',
      data: {
        labels: ['Fuel', 'Time'],
        datasets: [{
          data: [data.cost_breakdown.fuel, data.cost_breakdown.time],
          backgroundColor: ['#0d6efd', '#20c997']
        }]
      },
      options: { responsive: true }
    });
  } catch (e) {
    alert(e.message);
  } finally {
    setLoading(false);
  }
}

async function bookmarkPlace(btn) {
  const lat = parseFloat(btn.getAttribute('data-lat'));
  const lon = parseFloat(btn.getAttribute('data-lon'));
  const name = decodeURIComponent(btn.getAttribute('data-name') || '');
  const category = decodeURIComponent(btn.getAttribute('data-cat') || '');
  const external_id = btn.getAttribute('data-id') || null;
  const city = (currentLocation && currentLocation.name) || '';

  const res = await fetch('/api/bookmarks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ city, name, category, lat, lon, external_id })
  });
  if (res.ok) {
    loadBookmarks();
  }
}

async function loadBookmarks() {
  const res = await fetch('/api/bookmarks');
  const data = await res.json();
  const container = document.getElementById('bookmarks');
  container.innerHTML = '';
  if (res.ok) {
    if (!data.bookmarks.length) {
      container.innerHTML = '<div class="text-muted small">No bookmarks yet</div>';
      return;
    }
    data.bookmarks.forEach(b => {
      const div = document.createElement('div');
      div.className = 'd-flex justify-content-between align-items-center border rounded p-2 mb-2';
      div.innerHTML = `
        <div>
          <div class="fw-semibold">${b.name}</div>
          <div class="text-muted small">${b.city}</div>
        </div>
        <button class="btn btn-sm btn-outline-danger" onclick="deleteBookmark(${b.id})">Delete</button>
      `;
      container.appendChild(div);
    });
  }
}

async function deleteBookmark(id) {
  const res = await fetch(`/api/bookmarks/${id}`, { method: 'DELETE' });
  if (res.ok) loadBookmarks();
}

function setLoading(state) {
  const btn = document.getElementById('searchBtn');
  btn.disabled = !!state;
  btn.textContent = state ? 'Searching...' : 'Search';
}

window.addEventListener('DOMContentLoaded', () => {
  initMap();
  document.getElementById('searchBtn').addEventListener('click', searchCity);
  document.getElementById('costBtn').addEventListener('click', estimateCost);
  document.querySelectorAll('.place-filter').forEach(btn => {
    btn.addEventListener('click', (e) => loadPlaces(btn.getAttribute('data-cat')));
  });
  document.getElementById('refreshBookmarks').addEventListener('click', loadBookmarks);
  loadBookmarks();
});