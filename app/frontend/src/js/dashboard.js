/* ═══════════════════════════════════════════════
   dashboard.js  —  Supply Chain Analysis
   Logic for dashboard.html
   Depends on: data.js  +  Chart.js (CDN)
═══════════════════════════════════════════════ */

/* ── LOCAL STATE ── */
let selectedShipping = 'Standard Class';
let chartInstance    = null;

/* ═══════════════════════════════════════════════
   BOOT — Read persisted selection
═══════════════════════════════════════════════ */
function boot() {
  const product  = State.getProduct();
  const category = State.getCategory();

  if (!product || !category) {
    /* Nothing selected — redirect back */
    window.location.href = 'index.html';
    return;
  }

  renderProductBadge(product, category);
  initMetrics(category);
  initChart(category);
  initShippingTabs();
  initPredictBtn();
}

/* ═══════════════════════════════════════════════
   PRODUCT BADGE
═══════════════════════════════════════════════ */
function renderProductBadge(product, category) {
  const badge = document.getElementById('product-badge');
  if (!badge) return;
  badge.innerHTML = `
    <strong>${product.name}</strong>
    <span style="opacity:0.5">·</span>
    <span>${category}</span>
    <span style="opacity:0.5">·</span>
    <span>$${product.price.toFixed(2)}</span>`;
}

/* ═══════════════════════════════════════════════
   METRICS — Animated count-up
═══════════════════════════════════════════════ */
function initMetrics(category) {
  const data = TREND_DATA[category];
  if (!data) return;

  const rev = data.revenue[data.revenue.length - 1];
  const sal = data.sales[data.sales.length - 1];

  animateNumber('total-revenue', rev);
  animateNumber('total-sales',   sal);
}

function animateNumber(id, target) {
  const el = document.getElementById(id);
  if (!el) return;

  const duration = 1300;
  const start    = performance.now();

  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    const ease     = 1 - Math.pow(1 - progress, 3); /* ease-out cubic */
    const val      = Math.round(ease * target);
    el.textContent = val.toLocaleString('en-US');
    if (progress < 1) requestAnimationFrame(step);
  }

  requestAnimationFrame(step);
}

/* ═══════════════════════════════════════════════
   TREND CHART
═══════════════════════════════════════════════ */
function initChart(category) {
  const data = TREND_DATA[category];
  if (!data) return;

  const canvas = document.getElementById('trend-chart');
  if (!canvas) return;

  if (chartInstance) chartInstance.destroy();

  chartInstance = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [
        {
          label: 'Revenue ($)',
          data: data.revenue,
          borderColor:          'rgba(26,24,20,0.75)',
          backgroundColor:      'rgba(26,24,20,0.05)',
          borderWidth:          2,
          pointBackgroundColor: 'rgba(26,24,20,0.85)',
          pointRadius:          4,
          pointHoverRadius:     6,
          tension:              0.42,
          fill:                 true,
          yAxisID: 'yRev'
        },
        {
          label: 'Units Sold',
          data: data.sales,
          borderColor:          'rgba(26,24,20,0.35)',
          backgroundColor:      'transparent',
          borderWidth:          1.5,
          borderDash:           [5, 4],
          pointBackgroundColor: 'rgba(26,24,20,0.5)',
          pointRadius:          3,
          tension:              0.42,
          fill:                 false,
          yAxisID: 'ySales'
        }
      ]
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      interaction:         { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display:  true,
          position: 'top',
          labels: {
            font:      { family: 'Cormorant Garamond', size: 11 },
            color:     '#6b6560',
            boxWidth:  12,
            padding:   16
          }
        },
        tooltip: {
          bodyFont:  { family: 'IM Fell English', size: 13 },
          titleFont: { family: 'Cormorant Garamond', size: 11 },
          callbacks: {
            label(ctx) {
              return ctx.dataset.yAxisID === 'yRev'
                ? ` $${ctx.parsed.y.toLocaleString()}`
                : ` ${ctx.parsed.y.toLocaleString()} units`;
            }
          }
        }
      },
      scales: {
        x: {
          grid:  { display: false },
          ticks: { font: { family: 'Cormorant Garamond', size: 11 }, color: '#6b6560' }
        },
        yRev: {
          position: 'left',
          grid:     { color: 'rgba(26,24,20,0.06)' },
          ticks: {
            font:     { family: 'Cormorant Garamond', size: 10 },
            color:    '#6b6560',
            callback: v => '$' + (v / 1000).toFixed(0) + 'k'
          }
        },
        ySales: {
          position: 'right',
          grid:     { display: false },
          ticks: {
            font:  { family: 'Cormorant Garamond', size: 10 },
            color: '#9b9590'
          }
        }
      }
    }
  });
}

/* ═══════════════════════════════════════════════
   SHIPPING TABS
═══════════════════════════════════════════════ */
function initShippingTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(btn => {
    btn.addEventListener('click', function () {
      tabs.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      selectedShipping = this.dataset.mode;
    });
  });
}

/* ═══════════════════════════════════════════════
   PREDICT LATE RISK
═══════════════════════════════════════════════ */
function initPredictBtn() {
  const btn = document.getElementById('btn-predict');
  if (btn) btn.addEventListener('click', predictRisk);
}

function predictRisk() {
  const btn    = document.getElementById('btn-predict');
  const daysEl = document.getElementById('result-days');
  const riskEl = document.getElementById('result-risk');

  /* Loading state */
  btn.innerHTML = '<span class="spinner"></span> Predicting…';
  btn.disabled  = true;

  setTimeout(() => {
    const result = RISK_TABLE[selectedShipping];

    /* Update values */
    daysEl.textContent = result.days + ' Days';
    riskEl.textContent = result.risk + ' %';

    /* Risk colour coding */
    riskEl.className = 'result-value ' + (
      result.risk <= 8  ? 'risk-low'  :
      result.risk <= 18 ? 'risk-mid'  : 'risk-high'
    );

    /* Pop animation */
    [daysEl, riskEl].forEach(el => {
      el.style.transform = 'scale(0.82)';
      requestAnimationFrame(() => {
        el.style.transition = 'transform 0.4s cubic-bezier(0.34,1.56,0.64,1)';
        el.style.transform  = 'scale(1)';
      });
    });

    /* Reset button */
    btn.innerHTML = 'Predict Late Risk';
    btn.disabled  = false;
  }, 1450);
}

/* ═══════════════════════════════════════════════
   BACK NAVIGATION
═══════════════════════════════════════════════ */
function goBack() {
  window.location.href = '/app/frontend/src/pages/index.html';
}

/* ═══════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  boot();

  const btnBack = document.getElementById('btn-back');
  if (btnBack) btnBack.addEventListener('click', goBack);
});
