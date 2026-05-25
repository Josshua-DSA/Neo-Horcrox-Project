import { apiGet, formatMetric, text } from "../api.js";

const summaryTarget = document.querySelector("[data-dashboard-summary]");
const riskTarget = document.querySelector("[data-risk-by-market]");
const salesTarget = document.querySelector("[data-sales-by-category]");
const shippingTarget = document.querySelector("[data-shipping-performance]");
const statusTarget = document.querySelector("[data-status]");

init();

async function init() {
  if (!summaryTarget || !riskTarget || !salesTarget || !shippingTarget) return;
  try {
    const filters = await apiGet("/dashboard/filters");
    ensureRiskLevelFilter();
    applyDateRange(filters.date_range || {});
    renderFilters(filters);
    bindFilters();
    await loadDashboard();
  } catch (error) {
    setStatus(error.message);
  }
}

async function loadDashboard() {
  try {
    setStatus("Loading dashboard data...");
    const query = buildDashboardQuery();
    const [summary, risk, sales, shipping] = await Promise.all([
      apiGet(withQuery("/dashboard/summary", query)),
      apiGet(withQuery("/dashboard/risk-by-market", query)),
      apiGet(withQuery("/dashboard/sales-by-category", query)),
      apiGet(withQuery("/dashboard/shipping-performance", query)),
    ]);

    renderSummary(summary);
    riskTarget.innerHTML = renderRows(risk.data || [], ["market", "total_orders", "late_orders", "late_rate"]);
    salesTarget.innerHTML = renderRows(sales.data || [], ["category_name", "total_sales", "order_count"]);
    shippingTarget.innerHTML = renderRows(shipping.data || [], ["shipping_mode", "order_count", "late_rate", "avg_shipping_days"]);
    setStatus(`Source: ${summary.source || "api"}`);
  } catch (error) {
    setStatus(error.message);
  }
}

function ensureRiskLevelFilter() {
  const form = document.querySelector("#dashboard-filters");
  if (!form || form.querySelector("[data-filter='risk_levels']")) return;
  form.insertAdjacentHTML("beforeend", `
    <label class="filter-field">
      <span>Risk Level</span>
      <select data-filter="risk_levels"><option>All Risk Level</option></select>
    </label>
  `);
}

function applyDateRange(range) {
  const inputs = document.querySelectorAll("#dashboard-filters input[type='date']");
  if (inputs[0] && range.start) {
    inputs[0].min = range.start;
    inputs[0].value = range.start;
  }
  if (inputs[1] && range.end) {
    inputs[1].max = range.end;
    inputs[1].value = range.end;
  }
}

function bindFilters() {
  const form = document.querySelector("#dashboard-filters");
  if (!form) return;
  form.querySelectorAll("select, input[type='date']").forEach((field) => {
    field.addEventListener("change", loadDashboard);
  });
}

function buildDashboardQuery() {
  const params = new URLSearchParams();
  const selectMap = {
    markets: "market",
    order_regions: "order_region",
    order_countries: "order_country",
    shipping_modes: "shipping_mode",
    categories: "category",
    departments: "department",
    segments: "segment",
    statuses: "status",
    risk_levels: "risk_level",
  };

  document.querySelectorAll("[data-filter]").forEach((select) => {
    const param = selectMap[select.dataset.filter];
    if (param && select.value) params.set(param, select.value);
  });

  const dates = document.querySelectorAll("#dashboard-filters input[type='date']");
  if (dates[0]?.value) params.set("start_date", dates[0].value);
  if (dates[1]?.value) params.set("end_date", dates[1].value);

  return params.toString();
}

function withQuery(path, query) {
  return query ? `${path}?${query}` : path;
}

function renderSummary(summary) {
  const cards = [
    ["Total Orders", formatMetric(summary.total_orders), "All recorded order transactions."],
    ["Total Sales", formatMetric(summary.total_sales, "currency"), "Gross sales from selected scope."],
    ["Late Shipment Rate", formatMetric(summary.late_rate, "percent"), "Shipment ratio marked as late."],
    ["Average Shipping Delay", `${formatMetric(summary.avg_shipping_delay)} days`, "Average delivery delay duration."],
    ["High Risk Shipment Count", formatMetric(summary.high_risk_shipments), "Shipments classified as high risk."],
    ["Total Profit", formatMetric(summary.total_profit, "currency"), "Profit after selected filters."],
    ["Average Discount Rate", formatMetric(summary.avg_discount_rate, "percent"), "Average discount across orders."],
  ];

  summaryTarget.innerHTML = cards.map(([label, value, note]) => `
    <article class="neo-card kpi-card">
      <span class="label-caps">${label}</span>
      <strong>${value}</strong>
      <p>${note}</p>
    </article>
  `).join("");
}

function renderFilters(filters) {
  document.querySelectorAll("[data-filter]").forEach((select) => {
    const key = select.dataset.filter;
    const first = select.querySelector("option")?.textContent || "All";
    const values = filters[key] || [];
    select.innerHTML = [`<option value="">${first}</option>`, ...values.map((value) => (
      `<option value="${escapeAttribute(value)}">${text(value)}</option>`
    ))].join("");
  });
}

function renderRows(rows, keys) {
  if (!rows.length) return `<tr><td colspan="${keys.length}">No data.</td></tr>`;
  return rows.map((row) => `
    <tr>
      ${keys.map((key) => `<td>${formatCell(key, row[key])}</td>`).join("")}
    </tr>
  `).join("");
}

function formatCell(key, value) {
  if (key.includes("rate")) return formatMetric(value, "percent");
  if (key.includes("sales")) return formatMetric(value, "currency");
  if (typeof value === "number") return formatMetric(value);
  return text(value);
}

function setStatus(message) {
  if (statusTarget) statusTarget.textContent = message;
}

function escapeAttribute(value) {
  return String(value ?? "").replaceAll('"', "&quot;");
}
