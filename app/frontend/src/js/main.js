/* ═══════════════════════════════════════════════
   main.js  —  Supply Chain Analysis
   Logic for index.html (Main / Landing page)
   Depends on: data.js
═══════════════════════════════════════════════ */

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
