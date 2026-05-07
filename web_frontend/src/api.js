/* Giữ nguyên 100% — không sửa bất kỳ dòng nào */
const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export const apiBase = API_BASE;

async function handleResponse(res) {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

export function fetchHealth() {
  return fetch(`${API_BASE}/health`).then(handleResponse);
}

export function fetchConfig() {
  return fetch(`${API_BASE}/config`).then(handleResponse);
}

export function fetchStats() {
  return fetch(`${API_BASE}/stats`).then(handleResponse);
}

export function fetchBenchmark() {
  return fetch(`${API_BASE}/benchmark`).then(handleResponse);
}

export function fetchHistory(date = "") {
  const query = date ? `?date=${encodeURIComponent(date)}` : "";
  return fetch(`${API_BASE}/history${query}`).then(handleResponse);
}

export function postTrigger() {
  return fetch(`${API_BASE}/trigger`, { method: "POST" }).then(handleResponse);
}

export function postContinue() {
  return fetch(`${API_BASE}/continue`, { method: "POST" }).then(handleResponse);
}

export function postMode(mode) {
  return fetch(`${API_BASE}/mode`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  }).then(handleResponse);
}

export function postConfig(payload) {
  return fetch(`${API_BASE}/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(handleResponse);
}

export function setDemoPlc() {
  return fetch(`${API_BASE}/plc/demo`, { method: "POST" }).then(handleResponse);
}

export function setRealPlc(payload) {
  return fetch(`${API_BASE}/plc/real`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(handleResponse);
}

export function clearHistory() {
  return fetch(`${API_BASE}/history`, { method: "DELETE" }).then(handleResponse);
}

export function exportHistoryUrl(date = "") {
  const query = date ? `?date=${encodeURIComponent(date)}` : "";
  return `${API_BASE}/history/export${query}`;
}

export function monitorWsUrl() {
  if (API_BASE.startsWith("https://")) {
    return API_BASE.replace("https://", "wss://") + "/ws/monitor";
  }
  return API_BASE.replace("http://", "ws://") + "/ws/monitor";
}
