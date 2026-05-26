import { apiGet, formatMetric, text } from "../api.js";
import { enhanceGlassSelect, refreshGlassSelect } from "../glassSelect.js";

const state = {
  categories: [],
  products: [],
  selectedCategoryId: "",
  selectedCandidateId: "",
};

const categorySelect = document.querySelector("[data-category-select]");
const productTable = document.querySelector("[data-product-table]");
const detailPanel = document.querySelector("[data-product-detail]");
const statusNode = document.querySelector("[data-status]");
const nextButton = document.querySelector("#btn-next");

init();

async function init() {
  if (!categorySelect || !productTable || !detailPanel) return;
  setStatus("Loading supplier metrics...");
  nextButton?.classList.add("is-disabled");

  try {
    const categories = await apiGet("/supplier-selection/categories");
    state.categories = categories.data || [];
    renderCategoryOptions(state.categories);
    setStatus(`${formatMetric(categories.total || 0)} categories loaded from metrics CSV`);
    if (state.categories.length) {
      categorySelect.value = state.categories[0].category_id;
      refreshGlassSelect(categorySelect);
      await loadProducts(state.categories[0].category_id);
    }
  } catch (error) {
    categorySelect.innerHTML = `<option value="">Failed loading categories</option>`;
    enhanceGlassSelect(categorySelect);
    renderEmpty(error.message);
    setStatus(error.message);
  }

  categorySelect.addEventListener("change", () => {
    const categoryId = categorySelect.value;
    if (categoryId) loadProducts(categoryId);
  });
}

function renderCategoryOptions(categories) {
  categorySelect.innerHTML = [
    `<option value="">Search / Select Category...</option>`,
    ...categories.map((category) => (
      `<option value="${escapeAttribute(category.category_id)}">${text(category.category_name)} (${formatMetric(category.total_candidates)})</option>`
    )),
  ].join("");
  enhanceGlassSelect(categorySelect);
}

async function loadProducts(categoryId) {
  state.selectedCategoryId = categoryId;
  state.selectedCandidateId = "";
  nextButton?.classList.add("is-disabled");
  productTable.innerHTML = `<tr class="empty-row"><td colspan="7">Loading candidates...</td></tr>`;
  detailPanel.innerHTML = `<p class="label-caps">Selected Product Detail</p><p class="body-serif">Loading candidate data from metrics CSV.</p>`;

  try {
    const products = await apiGet(`/supplier-selection/categories/${encodeURIComponent(categoryId)}/products?limit=25&include_rejected=true`);
    state.products = products.data || [];
    renderProducts(state.products);
    setStatus(`${formatMetric(products.total || 0)} candidates displayed`);
    if (state.products.length) {
      await selectCandidate(state.products[0].candidate_id);
    }
  } catch (error) {
    renderEmpty(error.message);
    setStatus(error.message);
  }
}

function renderProducts(products) {
  if (!products.length) {
    renderEmpty("No candidate data for this category.");
    return;
  }

  productTable.innerHTML = products.map((item) => `
    <tr data-candidate-id="${escapeAttribute(item.candidate_id)}">
      <td>${text(item.final_rank_in_category)}</td>
      <td>${text(item.candidate_name)}</td>
      <td>${text(item.recommendation)}</td>
      <td><span class="${riskClass(item.risk_level)}">${text(item.risk_level)}</span></td>
      <td>${formatMetric(item.topsis_score)}</td>
      <td>${formatMetric(item.late_rate, "percent")}</td>
      <td>${formatMetric(item.total_sales, "currency")}</td>
    </tr>
  `).join("");

  productTable.querySelectorAll("tr[data-candidate-id]").forEach((row) => {
    row.addEventListener("click", () => selectCandidate(row.dataset.candidateId));
  });
}

async function selectCandidate(candidateId) {
  state.selectedCandidateId = candidateId;
  productTable.querySelectorAll("tr[data-candidate-id]").forEach((row) => {
    row.classList.toggle("is-active", row.dataset.candidateId === String(candidateId));
  });
  detailPanel.innerHTML = `<p class="label-caps">Selected Product Detail</p><p class="body-serif">Loading profile...</p>`;

  try {
    const detail = await apiGet(`/supplier-selection/products/${encodeURIComponent(candidateId)}`);
    localStorage.setItem("selectedSupplierCandidate", JSON.stringify(detail));
    renderDetail(detail);
    nextButton?.classList.remove("is-disabled");
  } catch (error) {
    detailPanel.innerHTML = `<p class="label-caps">Selected Product Detail</p><p class="body-serif">${text(error.message)}</p>`;
  }
}

function renderDetail(detail) {
  const candidate = detail.candidate || {};
  const dataset = detail.dataset_profile || {};
  const summary = dataset.summary || {};
  const metrics = [
    ["Category", candidate.category_name],
    ["Product", candidate.candidate_name],
    ["Recommendation", candidate.recommendation],
    ["Risk level", candidate.risk_level],
    ["Risk score", formatMetric(candidate.risk_score)],
    ["TOPSIS", formatMetric(candidate.topsis_score)],
    ["Orders", formatMetric(candidate.total_orders)],
    ["Sales", formatMetric(candidate.total_sales, "currency")],
    ["Late rate", formatMetric(candidate.late_rate, "percent")],
    ["Raw trend orders", formatMetric(summary.total_orders)],
  ];

  detailPanel.innerHTML = `
    <p class="label-caps">Selected Product Detail</p>
    <h2>${text(candidate.candidate_name)}</h2>
    <dl class="detail-grid">
      ${metrics.map(([label, value]) => `<div><dt>${label}</dt><dd>${text(value)}</dd></div>`).join("")}
    </dl>
  `;
}

function renderEmpty(message) {
  productTable.innerHTML = `<tr class="empty-row"><td colspan="7">${text(message)}</td></tr>`;
}

function setStatus(message) {
  if (statusNode) statusNode.textContent = message;
}

function riskClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("low")) return "risk-low";
  if (normalized.includes("medium")) return "risk-mid";
  if (normalized.includes("high")) return "risk-high";
  return "";
}

function escapeAttribute(value) {
  return String(value ?? "").replaceAll('"', "&quot;");
}
