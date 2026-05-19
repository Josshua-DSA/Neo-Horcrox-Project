<<<<<<< HEAD
/* ═══════════════════════════════════════════════
   main.js  —  Supply Chain Analysis
   Logic for index.html (Main / Landing page)
   Depends on: data.js
═══════════════════════════════════════════════ */
=======
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const formatNumber = new Intl.NumberFormat("id-ID", { maximumFractionDigits: 2 });
const formatPercent = new Intl.NumberFormat("id-ID", {
  style: "percent",
  maximumFractionDigits: 1,
});

async function apiGet(path) {
  const response = await fetch(`${apiBaseUrl}${path}`);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function text(value, fallback = "-") {
  return value === null || value === undefined || value === "" ? fallback : String(value);
}

function setStatus(message) {
  const node = document.querySelector("[data-status]");
  if (node) node.textContent = message;
}

async function initSupplierSelectionPage() {
  const categoryList = document.querySelector("[data-category-list]");
  const productTable = document.querySelector("[data-product-table]");
  const detailPanel = document.querySelector("[data-product-detail]");
  if (!categoryList || !productTable || !detailPanel) return;

  try {
    const categories = await apiGet("/supplier-selection/categories");
    renderCategories(categories.data || [], categoryList);
    setStatus(`${categories.total || 0} kategori tersedia`);
  } catch (error) {
    setStatus(error.message);
  }

  function renderCategories(categories, target) {
    target.innerHTML = "";
    categories.forEach((category, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "category-button";
      button.dataset.categoryId = category.category_id;
      button.innerHTML = `
        <span>${text(category.category_name)}</span>
        <small>${formatNumber.format(category.total_candidates)} kandidat</small>
      `;
      button.addEventListener("click", () => loadProducts(category.category_id, button));
      target.appendChild(button);
      if (index === 0) button.click();
    });
  }

  async function loadProducts(categoryId, activeButton) {
    document.querySelectorAll(".category-button").forEach((button) => {
      button.classList.toggle("is-active", button === activeButton);
    });
    productTable.innerHTML = `<tr><td colspan="7">Memuat data...</td></tr>`;
    detailPanel.innerHTML = `<p class="muted">Detail kandidat</p>`;
    try {
      const products = await apiGet(`/supplier-selection/categories/${categoryId}/products?limit=25`);
      renderProducts(products.data || []);
      setStatus(`${products.total || 0} kandidat ditampilkan`);
    } catch (error) {
      productTable.innerHTML = `<tr><td colspan="7">${error.message}</td></tr>`;
    }
  }

  function renderProducts(products) {
    productTable.innerHTML = products
      .map((item) => `
        <tr data-candidate-id="${item.candidate_id}">
          <td>${text(item.final_rank_in_category)}</td>
          <td>${text(item.candidate_name)}</td>
          <td>${text(item.recommendation)}</td>
          <td>${text(item.risk_level)}</td>
          <td>${item.topsis_score == null ? "-" : formatNumber.format(item.topsis_score)}</td>
          <td>${item.late_rate == null ? "-" : formatPercent.format(item.late_rate)}</td>
          <td>${item.total_sales == null ? "-" : formatNumber.format(item.total_sales)}</td>
        </tr>
      `)
      .join("");

    productTable.querySelectorAll("tr[data-candidate-id]").forEach((row) => {
      row.addEventListener("click", () => loadDetail(row.dataset.candidateId, row));
    });
  }

  async function loadDetail(candidateId, activeRow) {
    productTable.querySelectorAll("tr").forEach((row) => {
      row.classList.toggle("is-active", row === activeRow);
    });
    detailPanel.innerHTML = `<p class="muted">Memuat detail...</p>`;
    try {
      const detail = await apiGet(`/supplier-selection/products/${candidateId}`);
      renderDetail(detail.candidate || {});
    } catch (error) {
      detailPanel.innerHTML = `<p class="error">${error.message}</p>`;
    }
  }

  function renderDetail(candidate) {
    const metrics = [
      ["Kategori", candidate.category_name],
      ["Kandidat", candidate.candidate_name],
      ["Rekomendasi", candidate.recommendation],
      ["Risk level", candidate.risk_level],
      ["Risk score", candidate.risk_score],
      ["Topsis score", candidate.topsis_score],
      ["Total orders", candidate.total_orders],
      ["Total sales", candidate.total_sales],
      ["Late rate", candidate.late_rate == null ? null : formatPercent.format(candidate.late_rate)],
      ["Profit", candidate.total_profit],
    ];

    detailPanel.innerHTML = `
      <h2>${text(candidate.candidate_name)}</h2>
      <dl class="detail-grid">
        ${metrics.map(([label, value]) => `<div><dt>${label}</dt><dd>${text(value)}</dd></div>`).join("")}
      </dl>
    `;
  }
}

async function initDashboardPage() {
  const summaryTarget = document.querySelector("[data-dashboard-summary]");
  const riskTarget = document.querySelector("[data-risk-by-market]");
  const salesTarget = document.querySelector("[data-sales-by-category]");
  const shippingTarget = document.querySelector("[data-shipping-performance]");
  if (!summaryTarget || !riskTarget || !salesTarget || !shippingTarget) return;

  try {
    const [summary, risk, sales, shipping] = await Promise.all([
      apiGet("/dashboard/summary"),
      apiGet("/dashboard/risk-by-market"),
      apiGet("/dashboard/sales-by-category"),
      apiGet("/dashboard/shipping-performance"),
    ]);

    summaryTarget.innerHTML = `
      <article><span>Total orders</span><strong>${formatNumber.format(summary.total_orders || 0)}</strong></article>
      <article><span>Total sales</span><strong>${formatNumber.format(summary.total_sales || 0)}</strong></article>
      <article><span>Late rate</span><strong>${formatPercent.format(summary.late_rate || 0)}</strong></article>
      <article><span>Categories</span><strong>${formatNumber.format(summary.total_categories || 0)}</strong></article>
    `;
    riskTarget.innerHTML = renderRows(risk.data || [], ["market", "total_orders", "late_orders", "late_rate"]);
    salesTarget.innerHTML = renderRows(sales.data || [], ["category_name", "total_sales", "order_count"]);
    shippingTarget.innerHTML = renderRows(shipping.data || [], ["shipping_mode", "order_count", "late_rate", "avg_shipping_days"]);
    setStatus(`Sumber data: ${summary.source || "api"}`);
  } catch (error) {
    setStatus(error.message);
  }
}

function renderRows(rows, keys) {
  if (!rows.length) return `<tr><td colspan="${keys.length}">Tidak ada data.</td></tr>`;
  return rows
    .map((row) => `
      <tr>
        ${keys.map((key) => `<td>${formatCell(key, row[key])}</td>`).join("")}
      </tr>
    `)
    .join("");
}

function formatCell(key, value) {
  if (value === null || value === undefined) return "-";
  if (key.includes("rate")) return formatPercent.format(Number(value) || 0);
  if (typeof value === "number") return formatNumber.format(value);
  return text(value);
}

initSupplierSelectionPage();
initDashboardPage();
>>>>>>> prefix-app

/* ── LOCAL STATE ── */
let selectedProduct  = null;
let selectedCategory = null;

/* ═══════════════════════════════════════════════
   FEATURE ITEMS — Scroll-triggered slide-in
═══════════════════════════════════════════════ */
function initFeatureAnimations() {
  const items = document.querySelectorAll('.feature-item');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const delay = parseInt(entry.target.dataset.delay || 0);
        setTimeout(() => entry.target.classList.add('visible'), delay);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  items.forEach(el => observer.observe(el));
}

/* ═══════════════════════════════════════════════
   CATEGORY SELECT → Populate Products Table
═══════════════════════════════════════════════ */
function initCategorySelect() {
  const select = document.getElementById('category-select');
  if (!select) return;

  select.addEventListener('change', function () {
    selectedCategory = this.value;
    selectedProduct  = null;
    populateTable(selectedCategory);
  });
}

function populateTable(cat) {
  const tbody = document.getElementById('products-tbody');
  if (!tbody) return;

  tbody.innerHTML = '';

  if (!cat || !PRODUCTS[cat]) {
    tbody.innerHTML = `
      <tr class="empty-row">
        <td colspan="2">Select a category to view products</td>
      </tr>`;
    return;
  }

  const prods = PRODUCTS[cat];

  prods.forEach((p, i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${p.name}</td>
      <td>$${p.price.toFixed(2)}</td>`;

    tr.addEventListener('click', () => {
      document.querySelectorAll('#products-tbody tr')
        .forEach(r => r.classList.remove('selected'));
      tr.classList.add('selected');
      selectedProduct = p;
    });

    tbody.appendChild(tr);

    /* Stagger row entrance */
    tr.style.opacity   = '0';
    tr.style.transform = 'translateY(8px)';
    tr.style.transition = `opacity 0.3s ease ${i * 55}ms, transform 0.3s ease ${i * 55}ms`;
    requestAnimationFrame(() => {
      tr.style.opacity   = '1';
      tr.style.transform = 'translateY(0)';
    });
  });
}

/* ═══════════════════════════════════════════════
   NAVIGATION → Go to Dashboard
═══════════════════════════════════════════════ */
function goToDashboard() {
  if (!selectedProduct) {
    /* Shake the table wrapper as feedback */
    const wrap = document.querySelector('.neo-table-wrap');
    if (wrap) {
      wrap.style.animation = 'none';
      wrap.style.transform = 'translateX(6px)';
      setTimeout(() => {
        wrap.style.transition = 'transform 0.35s ease';
        wrap.style.transform  = 'translateX(0)';
      }, 80);
    }
    alert('Pilih produk terlebih dahulu untuk melanjutkan analisis.');
    return;
  }

  /* Persist selection for dashboard page */
  State.saveSelection(selectedCategory, selectedProduct);

  /* Navigate */
  window.location.href = '/app/frontend/src/pages/dashboard.html';
}

/* ═══════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  initFeatureAnimations();
  initCategorySelect();

  /* Wire next button */
  const btnNext = document.getElementById('btn-next');
  if (btnNext) btnNext.addEventListener('click', goToDashboard);
});
