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
    const [filters, summary, risk, sales, shipping] = await Promise.all([
      apiGet("/dashboard/filters"),
      apiGet("/dashboard/summary"),
      apiGet("/dashboard/risk-by-market"),
      apiGet("/dashboard/sales-by-category"),
      apiGet("/dashboard/shipping-performance"),
    ]);

    renderFilters(filters);
    renderSummary(summary);
    riskTarget.innerHTML = renderRows(risk.data || [], ["market", "total_orders", "late_orders", "late_rate"]);
    salesTarget.innerHTML = renderRows(sales.data || [], ["category_name", "total_sales", "order_count"]);
    shippingTarget.innerHTML = renderRows(shipping.data || [], ["shipping_mode", "order_count", "late_rate", "avg_shipping_days"]);
    setStatus(`Source: ${summary.source || "api"}`);
  } catch (error) {
    setStatus(error.message);
  }
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
