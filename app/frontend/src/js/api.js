const viteEnv = import.meta.env || {};

export const apiBaseUrl = viteEnv.VITE_API_BASE_URL || "http://localhost:8017/api/v1";

export const numberFormatter = new Intl.NumberFormat("id-ID", {
  maximumFractionDigits: 2,
});

export const currencyFormatter = new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export const percentFormatter = new Intl.NumberFormat("id-ID", {
  style: "percent",
  maximumFractionDigits: 1,
});

export async function apiGet(path) {
  // Memastikan format path selalu diawali dengan /
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  
  // Memastikan apiBaseUrl tidak diakhiri dengan / sebelum digabung
  const cleanBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl.slice(0, -1) : apiBaseUrl;

  const response = await fetch(`${cleanBaseUrl}${cleanPath}`);
  return parseResponse(response);
}

export async function apiPost(path, payload) {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const cleanBaseUrl = apiBaseUrl.endsWith("/") ? apiBaseUrl.slice(0, -1) : apiBaseUrl;

  const response = await fetch(`${cleanBaseUrl}${cleanPath}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export function text(value, fallback = "-") {
  return value === null || value === undefined || value === "" ? fallback : String(value);
}

export function formatMetric(value, type = "number") {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return text(value);
  if (type === "currency") return currencyFormatter.format(number);
  if (type === "percent") return percentFormatter.format(number);
  return numberFormatter.format(number);
}

async function parseResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `Request failed: ${response.status}`);
  }
  return payload;
}
