const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling.
 */
async function apiFetch(path, options = {}) {
  const url = `${API_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }

  return res.json();
}

/**
 * Fetch full telemetry history for charts.
 * GET /api/telemetry/history
 */
export async function fetchTelemetryHistory() {
  return apiFetch('/api/telemetry/history');
}

/**
 * Fetch the most recent telemetry snapshot.
 * GET /api/telemetry/latest
 */
export async function fetchLatestTelemetry() {
  return apiFetch('/api/telemetry/latest');
}

/**
 * Fetch current system status (telemetry + sector states + risk).
 * GET /api/status
 */
export async function fetchStatus() {
  return apiFetch('/api/status');
}

/**
 * Send a manual command to a sector.
 * POST /api/commands/  { sector_id, action }
 */
export async function sendCommand(sectorId, action) {
  return apiFetch('/api/commands/', {
    method: 'POST',
    body: JSON.stringify({ sector_id: sectorId, action }),
  });
}

/**
 * Run a stress simulation scenario.
 * POST /api/simulate  { solar_generation, battery_level, lunar_hour }
 */
export async function sendSimulation(data) {
  return apiFetch('/api/simulate', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
