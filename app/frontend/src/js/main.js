/* ═══════════════════════════════════════════════
   main.js  —  Supply Chain Analysis
   Logic for index.html (Main / Landing page)
═══════════════════════════════════════════════ */

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

document.addEventListener('DOMContentLoaded', () => {
  initFeatureAnimations();
});
