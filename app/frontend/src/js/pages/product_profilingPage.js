import { apiGet, apiPost, formatMetric, text } from "../api.js";

const selected = readSelectedCandidate();
const productBadge = document.querySelector("#product-badge");
const revenueNode = document.querySelector("#total-revenue");
const quantityNode = document.querySelector("#total-sales");
const trendStatus = document.querySelector("#trend-status");
const statusNode = document.querySelector("#profile-status");
const shippingTabs = document.querySelector("#shipping-tabs");
const resultDays = document.querySelector("#result-days");
const resultRisk = document.querySelector("#result-risk");
const predictButton = document.querySelector("#btn-predict");
const forecastButton = document.querySelector("#btn-forecast");
const forecastMarket = document.querySelector("#forecast-market");
const forecastSummary = document.querySelector("#forecast-summary");
const forecastList = document.querySelector("#forecast-list");
const chartCanvas = document.querySelector("#trend-chart");

let activeShippingMode = null;
let forecastOptions = { categories: [], markets: [] };

init();

async function init() {
  renderSelectedProduct();
  renderTrend();
  renderShippingModes();
  await loadForecastOptions();
  predictButton?.addEventListener("click", predictRisk);
  forecastButton?.addEventListener("click", runForecast);
}

function readSelectedCandidate() {
  try {
    return JSON.parse(localStorage.getItem("selectedSupplierCandidate") || "null");
  } catch {
    return null;
  }
}

function renderSelectedProduct() {
  const candidate = selected?.candidate || {};
  const summary = selected?.dataset_profile?.summary || {};
  if (!selected) {
    productBadge.innerHTML = `<span>Select a product from Supplier Selection first.</span>`;
    setStatus("No selected product found.");
    return;
  }

  productBadge.innerHTML = `
    <span>Selected:</span>
    <strong>${text(candidate.candidate_name)}</strong>
    <span>${text(candidate.category_name)}</span>
  `;
  revenueNode.textContent = formatMetric(summary.total_revenue ?? candidate.total_sales, "currency");
  quantityNode.textContent = formatMetric(summary.total_quantity ?? candidate.total_quantity ?? candidate.total_orders);
  setStatus("Product profile loaded from supplier metrics and raw dataset.");
}

function renderTrend() {
  const points = selected?.dataset_profile?.trend || [];
  if (!chartCanvas) return;
  const context = chartCanvas.getContext("2d");
  context.clearRect(0, 0, chartCanvas.width, chartCanvas.height);

  if (!points.length) {
    trendStatus.textContent = "no trend data";
    context.fillStyle = "#94a3b8";
    context.font = "14px 'Outfit', 'Inter', sans-serif";
    context.fillText("No historical trend for this product.", 24, 110);
    return;
  }

  trendStatus.textContent = `${points.length} monthly points`;
  const padding = 28;
  const maxRevenue = Math.max(...points.map((item) => Number(item.revenue) || 0), 1);
  const barWidth = (chartCanvas.width - padding * 2) / points.length - 8;

  // Draw subtle horizontal grid lines
  context.strokeStyle = "rgba(255, 255, 255, 0.05)";
  context.lineWidth = 1;
  context.setLineDash([5, 5]);
  for (let i = 1; i <= 3; i++) {
    const gridY = padding + ((chartCanvas.height - padding * 2) * i) / 4;
    context.beginPath();
    context.moveTo(padding, gridY);
    context.lineTo(chartCanvas.width - padding, gridY);
    context.stroke();
  }
  context.setLineDash([]); // Reset line dash

  // Draw bottom baseline
  context.strokeStyle = "rgba(255, 255, 255, 0.12)";
  context.lineWidth = 1.5;
  context.beginPath();
  context.moveTo(padding, chartCanvas.height - padding);
  context.lineTo(chartCanvas.width - padding, chartCanvas.height - padding);
  context.stroke();

  points.forEach((point, index) => {
    const value = Number(point.revenue) || 0;
    const height = ((chartCanvas.height - padding * 2) * value) / maxRevenue;
    const x = padding + index * (barWidth + 8);
    const y = chartCanvas.height - padding - height;

    // Draw bar gradient
    const gradient = context.createLinearGradient(x, y, x, chartCanvas.height - padding);
    gradient.addColorStop(0, "#00f2fe"); // Glowing cyan at top
    gradient.addColorStop(1, "rgba(129, 140, 248, 0.15)"); // Faded indigo at bottom
    context.fillStyle = gradient;
    context.fillRect(x, y, Math.max(8, barWidth), height);

    // Draw glowing top border for each bar
    context.strokeStyle = "#00f2fe";
    context.lineWidth = 2.5;
    context.beginPath();
    context.moveTo(x, y);
    context.lineTo(x + Math.max(8, barWidth), y);
    context.stroke();

    // Draw date labels
    context.fillStyle = "#94a3b8"; // Muted grey-blue
    context.font = "10px 'Outfit', 'Inter', sans-serif";
    context.fillText(String(point.date).slice(5), x, chartCanvas.height - 10);
  });
}

function renderShippingModes() {
  const modes = selected?.dataset_profile?.shipping_modes || [];
  const fallback = [
    { mode: "Standard Class", scheduled_days: 4 },
    { mode: "Second Class", scheduled_days: 2 },
    { mode: "First Class", scheduled_days: 1 },
    { mode: "Same Day", scheduled_days: 0 },
  ];
  const data = modes.length ? modes : fallback;
  activeShippingMode = data[0];
  shippingTabs.innerHTML = `<span class="tab-group-label">Choose Mode</span>`;
  data.forEach((item, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `tab-btn${index === 0 ? " active" : ""}`;
    button.dataset.mode = item.mode;
    button.innerHTML = `${text(item.mode)}<small>${formatMetric(item.scheduled_days)} days</small>`;
    button.addEventListener("click", () => {
      activeShippingMode = item;
      document.querySelectorAll(".tab-btn[data-mode]").forEach((node) => {
        node.classList.toggle("active", node === button);
      });
      resultDays.textContent = formatMetric(item.scheduled_days);
    });
    shippingTabs.appendChild(button);
  });
  resultDays.textContent = formatMetric(activeShippingMode?.scheduled_days ?? 0);
}

async function loadForecastOptions() {
  try {
    forecastOptions = await apiGet("/forecast/options");
    const markets = forecastOptions.markets || [];
    forecastMarket.innerHTML = markets.map((market) => `<option value="${escapeAttribute(market)}">${text(market)}</option>`).join("");
    const profileMarket = selected?.dataset_profile?.forecast_input?.market;
    if (profileMarket && markets.includes(profileMarket)) {
      forecastMarket.value = profileMarket;
    }
  } catch (error) {
    forecastSummary.textContent = error.message;
  }
}

async function predictRisk() {
  const riskInput = { ...(selected?.dataset_profile?.risk_input || {}) };
  if (!Object.keys(riskInput).length) {
    setStatus("Risk input is unavailable for this product.");
    return;
  }

  riskInput["Shipping Mode"] = activeShippingMode?.mode || riskInput["Shipping Mode"];
  if (activeShippingMode?.scheduled_days !== null && activeShippingMode?.scheduled_days !== undefined) {
    riskInput.scheduled_days = activeShippingMode.scheduled_days;
  }

  predictButton.disabled = true;
  setStatus("Running late-risk model...");
  try {
    const response = await apiPost("/risk/predict", riskInput);
    const prediction = response.predictions?.[0];
    const percent = Number(prediction?.risk_percentage ?? (prediction?.late_probability || 0) * 100);
    resultRisk.textContent = `${formatMetric(percent)}%`;
    setStatus(`Prediction: ${prediction?.risk_label || "-"} using ${text(riskInput["Shipping Mode"])}.`);
  } catch (error) {
    setStatus(error.message);
  } finally {
    predictButton.disabled = false;
  }
}

async function runForecast() {
  const forecastInput = selected?.dataset_profile?.forecast_input || {};
  const category = forecastInput.category_name;
  const market = forecastMarket.value || forecastInput.market;
  if (!category || !market) {
    forecastSummary.textContent = "Forecast category or market is unavailable.";
    return;
  }

  forecastButton.disabled = true;
  forecastSummary.textContent = "Running registered forecast model...";
  try {
    const response = await apiPost("/forecast/predict", {
      category_name: category,
      market,
      periods: 14,
    });
    renderForecast(response);
  } catch (error) {
    forecastSummary.textContent = error.message;
    forecastList.innerHTML = "";
  } finally {
    forecastButton.disabled = false;
  }
}

function renderForecast(response) {
  const points = response.forecast || [];
  forecastSummary.textContent = `${text(response.category_name)} in ${text(response.market)} - model ${text(response.model_version)}`;
  forecastList.innerHTML = points.slice(0, 10).map((point) => `
    <div class="forecast-point">
      <strong>${formatMetric(point.predicted_sales, "currency")}</strong>
      <span>${text(point.date)}</span>
      <span>${formatMetric(point.lower_bound, "currency")} - ${formatMetric(point.upper_bound, "currency")}</span>
    </div>
  `).join("");
}

function setStatus(message) {
  if (statusNode) statusNode.textContent = message;
}

function escapeAttribute(value) {
  return String(value ?? "").replaceAll('"', "&quot;");
}
