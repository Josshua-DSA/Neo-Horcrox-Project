import { apiGet, apiPost, formatMetric, text } from "../api.js";
import { enhanceGlassSelect } from "../glassSelect.js";

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
let trendCoordinates = [];
let hoveredIndex = null;
let tooltipNode = null;

init();

async function init() {
  renderSelectedProduct();
  renderTrend();
  renderShippingModes();
  await loadForecastOptions();
  initChartEvents();
  predictButton?.addEventListener("click", predictRisk);
  forecastButton?.addEventListener("click", runForecast);
  await runForecast();
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
  trendCoordinates = [];
  if (!chartCanvas) return;
  const context = chartCanvas.getContext("2d");
  const width = chartCanvas.width;
  const height = chartCanvas.height;
  context.clearRect(0, 0, width, height);

  if (!points.length) {
    trendStatus.textContent = "no trend data";
    context.fillStyle = "#6b6560";
    context.font = "16px serif";
    context.fillText("No historical trend for this product.", 24, 110);
    return;
  }

  trendStatus.textContent = `${points.length} monthly points`;
  const padding = { top: 22, right: 22, bottom: 34, left: 54 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const values = points.map((item) => Number(item.revenue) || 0);
  const maxRevenue = Math.max(...values, 1);
  const minRevenue = Math.min(...values, 0);
  const range = Math.max(maxRevenue - minRevenue, 1);
  const coordinates = points.map((point, index) => {
    const x = padding.left + (points.length === 1 ? chartWidth / 2 : (chartWidth * index) / (points.length - 1));
    const y = padding.top + chartHeight - (((Number(point.revenue) || 0) - minRevenue) / range) * chartHeight;
    return { x, y, point };
  });
  trendCoordinates = coordinates;

  drawTrendGrid(context, width, height, padding, chartHeight, chartWidth, maxRevenue, minRevenue);

  // Draw vertical guide line if a point is hovered
  if (hoveredIndex !== null && hoveredIndex >= 0 && hoveredIndex < coordinates.length) {
    const activePt = coordinates[hoveredIndex];
    context.strokeStyle = "rgba(255, 255, 255, 0.25)";
    context.lineWidth = 1.5;
    context.setLineDash([4, 4]);
    context.beginPath();
    context.moveTo(activePt.x, padding.top);
    context.lineTo(activePt.x, height - padding.bottom);
    context.stroke();
    context.setLineDash([]);
  }

  const gradient = context.createLinearGradient(0, padding.top, 0, height - padding.bottom);
  gradient.addColorStop(0, "rgba(26,24,20,0.24)");
  gradient.addColorStop(1, "rgba(26,24,20,0.02)");

  context.beginPath();
  coordinates.forEach(({ x, y }, index) => {
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  });
  context.lineTo(coordinates[coordinates.length - 1].x, height - padding.bottom);
  context.lineTo(coordinates[0].x, height - padding.bottom);
  context.closePath();
  context.fillStyle = gradient;
  context.fill();

  context.beginPath();
  coordinates.forEach(({ x, y }, index) => {
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  });
  context.lineWidth = 3;
  context.lineCap = "round";
  context.lineJoin = "round";
  context.strokeStyle = "rgba(26,24,20,0.82)";
  context.stroke();

  coordinates.forEach(({ x, y, point }, index) => {
    const isHovered = index === hoveredIndex;
    
    // Draw outer glowing aura for hovered point first (so it's under the main dot)
    if (isHovered) {
      context.beginPath();
      context.arc(x, y, 12, 0, Math.PI * 2);
      context.fillStyle = "rgba(255, 255, 255, 0.15)";
      context.fill();
    }

    context.beginPath();
    const radius = isHovered ? 6.5 : 4.5;
    context.arc(x, y, radius, 0, Math.PI * 2);
    context.fillStyle = isHovered ? "#ffffff" : "#f7f0e6";
    context.fill();
    context.lineWidth = isHovered ? 2.5 : 2;
    context.strokeStyle = isHovered ? "rgba(255, 255, 255, 1)" : "rgba(26,24,20,0.82)";
    context.stroke();

    if (index === 0 || index === coordinates.length - 1 || index % 3 === 0) {
      context.fillStyle = "#cecece"; // Brightened from #6b6560
      context.font = "10px serif";
      context.textAlign = "center";
      context.fillText(String(point.date).slice(5), x, height - 12);
    }
  });

  const last = coordinates[coordinates.length - 1];
  context.fillStyle = "#f5f5f5"; // Brightened from dark brown/black
  context.font = "bold 12px serif";
  context.textAlign = "right";
  context.fillText(formatMetric(last.point.revenue, "currency"), width - padding.right, Math.max(16, last.y - 10));
}

function drawTrendGrid(context, width, height, padding, chartHeight, chartWidth, maxRevenue, minRevenue) {
  context.strokeStyle = "rgba(255, 255, 255, 0.08)"; // Lighter grid lines
  context.lineWidth = 1;
  context.fillStyle = "#cecece"; // Brightened from #8b827a
  context.font = "10px serif";
  context.textAlign = "right";

  for (let index = 0; index <= 4; index += 1) {
    const ratio = index / 4;
    const y = padding.top + chartHeight * ratio;
    const value = maxRevenue - (maxRevenue - minRevenue) * ratio;

    context.beginPath();
    context.moveTo(padding.left, y);
    context.lineTo(width - padding.right, y);
    context.stroke();
    context.fillText(compactCurrency(value), padding.left - 10, y + 3);
  }

  context.strokeStyle = "rgba(255, 255, 255, 0.35)"; // Lighter axis lines
  context.beginPath();
  context.moveTo(padding.left, padding.top);
  context.lineTo(padding.left, height - padding.bottom);
  context.lineTo(padding.left + chartWidth, height - padding.bottom);
  context.stroke();
}

function compactCurrency(value) {
  const number = Number(value) || 0;
  if (Math.abs(number) >= 1000000) return `$${(number / 1000000).toFixed(1)}m`;
  if (Math.abs(number) >= 1000) return `$${Math.round(number / 1000)}k`;
  return `$${Math.round(number)}`;
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
  const profileMarket = getForecastInput().market;
  try {
    forecastOptions = await apiGet("/forecast/options");
    const markets = forecastOptions.markets || [];
    const optionMarkets = profileMarket && !markets.includes(profileMarket)
      ? [profileMarket, ...markets]
      : (markets.length ? markets : [profileMarket].filter(Boolean));
    forecastMarket.innerHTML = optionMarkets.map((market) => `<option value="${escapeAttribute(market)}">${text(market)}</option>`).join("");
    if (profileMarket && optionMarkets.includes(profileMarket)) {
      forecastMarket.value = profileMarket;
    }
  } catch (error) {
    forecastSummary.textContent = error.message;
    if (profileMarket) {
      forecastMarket.innerHTML = `<option value="${escapeAttribute(profileMarket)}">${text(profileMarket)}</option>`;
      forecastMarket.value = profileMarket;
    }
  }
  enhanceGlassSelect(forecastMarket);
}

async function predictRisk() {
  const riskInput = { ...(selected?.dataset_profile?.risk_input || {}) };
  if (!riskInput || (!riskInput["Latitude"] && !riskInput["Longitude"])) {
    setStatus("Risk input is unavailable for this product.");
    return;
  }

  // Override Shipping Mode and scheduled days from selected tab
  riskInput["Shipping Mode"] = activeShippingMode?.mode || riskInput["Shipping Mode"];
  if (activeShippingMode?.scheduled_days !== null && activeShippingMode?.scheduled_days !== undefined) {
    riskInput["Days for shipment (scheduled)"] = activeShippingMode.scheduled_days;
    riskInput.scheduled_days = activeShippingMode.scheduled_days;
  }

  // Inject current click hour dynamically
  const now = new Date();
  const currentHour = now.getHours();
  riskInput["order_hour"] = currentHour;
  
  // Remove static/None order_period so the backend feature builder computes it
  delete riskInput["order_period"];

  predictButton.disabled = true;
  setStatus("Running late-risk model...");
  try {
    const response = await apiPost("/risk/predict", riskInput);
    const prediction = response.predictions?.[0];
    if (prediction) {
      const isLate = prediction.risk_label === "yes";
      // Display correct percentage based on prediction label:
      // YES = probability of late (risk_percentage)
      // NO = probability of on-time (100 - risk_percentage)
      const percent = isLate 
        ? Number(prediction.risk_percentage)
        : Number(100 - prediction.risk_percentage);
      
      const labelText = isLate ? "YES — LATE RISK" : "NO — ON TIME";
      
      // Update container styling for the risk status
      const parentCard = resultRisk.closest(".result-card");
      if (parentCard) {
        parentCard.className = `glass-card result-card risk-${prediction.risk_label}`;
      }

      // Display the risk label and percentage beautifully
      resultRisk.innerHTML = `
        <span class="risk-label-${prediction.risk_label}">${labelText}</span>
        <span class="risk-percent">${formatMetric(percent)}%</span>
      `;
      
      // Add simulated order hour info to result card label
      const formatHour = String(currentHour).padStart(2, "0");
      const riskLabelNode = document.querySelector("#result-risk-label") || parentCard?.querySelector(".result-label");
      if (riskLabelNode) {
        riskLabelNode.innerHTML = `Late Risk <span style="display:block; font-size:0.7rem; margin-top:0.4rem; opacity:0.8; text-transform:none;">(Simulated Order Hour: ${formatHour}:00)</span>`;
      }

      setStatus(`Prediction: ${prediction.delivery_label || (isLate ? "Late Delivery Risk" : "On Time")} using ${text(riskInput["Shipping Mode"])}.`);
    } else {
      resultRisk.textContent = "-";
      setStatus("No predictions returned from model.");
    }
  } catch (error) {
    setStatus(error.message);
  } finally {
    predictButton.disabled = false;
  }
}

async function runForecast() {
  const forecastInput = getForecastInput();
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

function getForecastInput() {
  return selected?.forecast_input || selected?.dataset_profile?.forecast_input || {};
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

function createTooltip() {
  if (tooltipNode) return tooltipNode;
  tooltipNode = document.createElement("div");
  tooltipNode.className = "chart-tooltip";
  document.body.appendChild(tooltipNode);
  return tooltipNode;
}

function initChartEvents() {
  if (!chartCanvas) return;

  chartCanvas.addEventListener("mousemove", (event) => {
    if (!trendCoordinates.length) return;

    const rect = chartCanvas.getBoundingClientRect();
    const mouseX = (event.clientX - rect.left) * (chartCanvas.width / rect.width);
    const mouseY = (event.clientY - rect.top) * (chartCanvas.height / rect.height);

    let closestIndex = null;
    let minDistance = Infinity;

    trendCoordinates.forEach((coord, index) => {
      const dx = mouseX - coord.x;
      const dy = mouseY - coord.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < minDistance) {
        minDistance = dist;
        closestIndex = index;
      }
    });

    if (minDistance < 20 && closestIndex !== null) {
      if (hoveredIndex !== closestIndex) {
        hoveredIndex = closestIndex;
        renderTrend();
      }

      const activePt = trendCoordinates[hoveredIndex];
      const el = createTooltip();
      el.innerHTML = `
        <div class="chart-tooltip-date">${formatDateTooltip(activePt.point.date)}</div>
        <div class="chart-tooltip-value">${formatMetric(activePt.point.revenue, "currency")}</div>
      `;
      el.style.left = `${event.pageX + 15}px`;
      el.style.top = `${event.pageY - 15}px`;
      el.classList.add("is-visible");
    } else {
      if (hoveredIndex !== null) {
        hoveredIndex = null;
        renderTrend();
      }
      hideTooltip();
    }
  });

  chartCanvas.addEventListener("mouseleave", () => {
    if (hoveredIndex !== null) {
      hoveredIndex = null;
      renderTrend();
    }
    hideTooltip();
  });
}

function hideTooltip() {
  if (tooltipNode) {
    tooltipNode.classList.remove("is-visible");
  }
}

function formatDateTooltip(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString("id-ID", { month: "long", year: "numeric" });
}
