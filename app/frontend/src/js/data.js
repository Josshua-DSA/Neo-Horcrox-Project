/* ═══════════════════════════════════════════════
   data.js  —  Supply Chain Analysis
   Shared data constants & state management
   Used by both main.js and dashboard.js
═══════════════════════════════════════════════ */

/* ── PRODUCT CATALOGUE ── */
const PRODUCTS = {
  "Technology": [
    { name: "Apple Smart Phone, Full Size",    price: 1399.99 },
    { name: "Cisco TelePresence System EX90",  price: 1999.00 },
    { name: "Canon ImageCLASS 2200",           price: 1079.99 },
    { name: "Samsung Chromebook",              price:  244.99 },
    { name: "Plantronics CS510 Headset",       price:  349.50 },
    { name: "Brother Laser Printer HL-L2395DW",price:  229.99 },
    { name: "Logitech MX Master 3S Mouse",     price:   99.99 },
  ],
  "Furniture": [
    { name: "HON 5400 Series Task Chair",      price:  499.99 },
    { name: "Bretford CR4500 Series Cart",     price: 1299.00 },
    { name: "Office Star Executive Chair",     price:  299.99 },
    { name: "Safco Steel Wire Bookcase",       price:  219.99 },
    { name: "Sauder Classic Bookcase 5-Shelf", price:  139.99 },
    { name: "Bush Westfield Collection Desk",  price:  499.00 },
  ],
  "Office Supplies": [
    { name: "Avery Durable View Binder",       price:   12.99 },
    { name: "GBC DocuBind TL300 System",       price:  189.00 },
    { name: "Staples Copy Paper 500ct",        price:   39.99 },
    { name: "Mead Five Star Notebook",         price:    8.99 },
    { name: "Post-it Super Sticky Notes 12pk", price:   14.49 },
    { name: "Fellowes Powershred Shredder",    price:  299.00 },
  ]
};

/* ── TREND DATA PER CATEGORY ── */
const TREND_DATA = {
  "Technology": {
    labels:  ["2020", "2021", "2022", "2023", "2024"],
    revenue: [142000, 175000, 198000, 221000, 268000],
    sales:   [320, 395, 410, 450, 520]
  },
  "Furniture": {
    labels:  ["2020", "2021", "2022", "2023", "2024"],
    revenue: [88000, 95000, 107000, 119000, 135000],
    sales:   [210, 225, 240, 260, 295]
  },
  "Office Supplies": {
    labels:  ["2020", "2021", "2022", "2023", "2024"],
    revenue: [34000, 41000, 47000, 52000, 61000],
    sales:   [1800, 2100, 2350, 2600, 3000]
  }
};

/* ── RISK PREDICTION TABLE ── */
const RISK_TABLE = {
  "Standard Class": { days: 5, risk: 22 },
  "First Class":    { days: 3, risk: 8  },
  "Second Class":   { days: 4, risk: 15 },
  "Same Day":       { days: 1, risk: 4  }
};

/* ── SESSION STATE ── (persisted via sessionStorage)
   Keys:
     sca_product   → JSON: { name, price }
     sca_category  → string
─────────────────────────────────────────────────── */
const State = {
  saveSelection(category, product) {
    sessionStorage.setItem('sca_category', category);
    sessionStorage.setItem('sca_product',  JSON.stringify(product));
  },

  getCategory() {
    return sessionStorage.getItem('sca_category') || null;
  },

  getProduct() {
    const raw = sessionStorage.getItem('sca_product');
    try { return raw ? JSON.parse(raw) : null; }
    catch { return null; }
  },

  clear() {
    sessionStorage.removeItem('sca_category');
    sessionStorage.removeItem('sca_product');
  }
};
