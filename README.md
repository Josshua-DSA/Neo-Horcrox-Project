# Neo Horcrox Supply Chain Analytics

> **Decision Support System berbasis Machine Learning untuk Analitik Rantai Pasok**
>
> Mata Kuliah: MLOps | Semester 4 | Politeknik Elektronika Negeri Surabaya (PENS-EEPIS) | 2026

[![GitHub Repository](https://img.shields.io/badge/GitHub-Josshua--DSA%2FNeo--Horcrox--Project-blue?logo=github)](https://github.com/Josshua-DSA/Neo-Horcrox-Project)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Deploy-Docker%20Compose-2496ED?logo=docker)](https://docs.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2016-336791?logo=postgresql)](https://www.postgresql.org/)

---

Neo Horcrox adalah aplikasi analitik supply chain berbasis web yang membantu stakeholder melihat kondisi operasional, memilih produk/supplier terbaik, memprediksi risiko keterlambatan pengiriman, dan menjalankan demand forecast berdasarkan produk yang dipilih.

Project ini disusun sebagai sistem end-to-end:

- Frontend interaktif untuk stakeholder dan user bisnis.
- Backend FastAPI untuk API, business logic, dan model serving.
- PostgreSQL untuk database transaksional dan logging.
- CSV/JSON/model artifact untuk dashboard fallback, supplier ranking, risk model, dan forecast model.
- Docker Compose agar aplikasi dapat dijalankan secara konsisten di environment lokal.

---

## Quick Start

```powershell
git clone https://github.com/Josshua-DSA/Neo-Horcrox-Project
cd Neo-Horcrox-Project
docker compose up --build
```

Buka di browser:

| Layanan | URL |
| --- | --- |
| Frontend | http://localhost:5117 |
| API Docs (Swagger UI) | http://localhost:8017/docs |
| API Health Check | http://localhost:8017/api/v1/health |

---

## Executive Summary

Supply chain memiliki banyak titik keputusan: produk mana yang performanya terbaik, supplier mana yang paling aman, market mana yang memiliki risiko pengiriman tinggi, serta bagaimana proyeksi demand produk ke depan. Neo Horcrox menggabungkan dashboard analytics, supplier selection ranking, risk prediction, dan forecasting dalam satu alur pengguna yang sederhana.

Alur utama aplikasi:

1. Stakeholder membuka landing page.
2. User masuk ke dashboard dan membaca executive summary.
3. User memilih produk melalui Supplier Selection.
4. Sistem menampilkan kandidat produk/supplier terbaik berdasarkan ranking CSV/JSON.
5. User memilih produk.
6. Product Profiling otomatis menampilkan tren, menjalankan forecast demand, dan dapat memanggil prediksi risiko keterlambatan.

## Business Objective

Tujuan bisnis project ini adalah menjadi decision support system untuk supply chain analytics.

Fokus keputusan yang dibantu:

- Mengetahui total order, total sales, profit, discount rate, dan late shipment rate.
- Mengidentifikasi market, kategori, dan shipping mode dengan risiko keterlambatan tinggi.
- Memilih produk/supplier terbaik berdasarkan ranking multi-kriteria.
- Melihat profil historis produk yang dipilih.
- Menghasilkan demand forecast otomatis dari konteks produk terpilih.
- Memperkirakan risiko keterlambatan pengiriman menggunakan model machine learning.

## Current Application Scope

Fitur yang tersedia saat ini:

- Landing page sebagai pintu masuk aplikasi.
- Dashboard executive summary dengan filter interaktif.
- Supplier Selection berbasis kategori dan ranking produk.
- Product Profiling berbasis produk yang dipilih.
- Late shipment risk prediction via API.
- Demand forecast via API.
- PostgreSQL database service.
- Docker Compose untuk menjalankan full stack.
- API prefix utama `/api/v1` dan alias kompatibilitas `/api`.

## User Journey

```text
Landing Page
  |
  | Try your experience
  v
Dashboard
  |
  | Executive Summary:
  | - Total Orders
  | - Total Sales
  | - Late Shipment Rate
  | - Average Shipping Delay
  | - High Risk Shipment Count
  | - Total Profit
  | - Average Discount Rate
  |
  | Filters:
  | - Date Range
  | - Market
  | - Order Region
  | - Order Country
  | - Shipping Mode
  | - Category Name
  | - Department Name
  | - Customer Segment
  | - Order Status
  | - Risk Level
  |
  | Choose your Product
  v
Supplier Selection
  |
  | GET /api/v1/supplier-selection/categories
  | User selects category
  | GET /api/v1/supplier-selection/categories/{category_id}/products
  | User selects product
  | GET /api/v1/supplier-selection/products/{candidate_id}
  v
Product Profiling
  |
  | Uses selected product detail from localStorage
  | Uses forecast_input from backend response
  | POST /api/v1/forecast/predict
  | Optional: POST /api/v1/risk/predict
  v
Forecast, Trend, and Risk Insight
```

## High-Level Architecture

```text
Browser
  |
  | http://localhost:5117
  v
Vite Frontend
  |
  | REST API calls
  | http://localhost:8017/api/v1
  v
FastAPI Backend
  |           |
  |           | SQLAlchemy async
  |           v
  |       PostgreSQL
  |
  | Reads model artifacts
  v
model/artifacts/
  ├── champion_model/late_shipment_model.pkl   (Risk Model - XGBoost)
  ├── forecast/forecast_model.pkl              (Forecast Model - XGBoost Regressor)
  └── metrics/supplier_selection_outputs/      (AHP Ranking Output CSV/JSON)

FastAPI Backend
  |
  | Reads raw dataset fallback
  v
model/dataset/raw/DataCoSupplyChainDataset.csv
```

## Technology Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Frontend | HTML, CSS, JavaScript, Vite | Web interface and page routing |
| Backend | FastAPI, Uvicorn | API server and model serving |
| Database | PostgreSQL 16 | Transactional database and prediction logs |
| ORM | SQLAlchemy AsyncIO, asyncpg | PostgreSQL connection and queries |
| Data Processing | pandas, numpy | Dataset aggregation and feature preparation |
| ML Runtime | scikit-learn, xgboost, lightgbm | Risk and forecast artifact loading |
| Hyperparameter Tuning | Optuna | XGBoost champion model tuning |
| Container | Docker, Docker Compose | Local full-stack orchestration |

## Runtime Ports

Ports are intentionally moved away from common defaults to avoid conflicts.

| Service | Host URL / Port | Internal Container Port | Notes |
| --- | --- | --- | --- |
| Frontend | `http://localhost:5117` | `5117` | Vite dev server |
| API | `http://localhost:8017` | `8017` | FastAPI/Uvicorn |
| API Docs | `http://localhost:8017/docs` | `8017` | Swagger UI |
| API Health | `http://localhost:8017/api/v1/health` | `8017` | Backend health check |
| PostgreSQL | `localhost:5417` | `5432` | Host uses 5417, Docker network still uses 5432 |

Important note:

- `0.0.0.0:8017` in Uvicorn logs means the server listens on all network interfaces.
- Browser users should open `localhost`, not `0.0.0.0`.

## Repository Structure

```text
Neo-Horcrox-Project/
|-- .dockerignore
|-- .env.example
|-- .gitignore
|-- Dockerfile
|-- docker-compose.yaml
|-- README.md
|-- app/
|   |-- __init__.py
|   |-- requirements.txt
|   |-- backend/
|   |   |-- __init__.py
|   |   |-- config.py
|   |   |-- dashboard.py
|   |   |-- main.py
|   |   |-- model_loader.py
|   |   |-- core/
|   |   |   |-- config.py
|   |   |   |-- database.py
|   |   |   `-- model_registry.py
|   |   |-- routes/
|   |   |   |-- __init__.py
|   |   |   |-- dashboard_routes.py
|   |   |   |-- forecast_routes.py
|   |   |   |-- health.py
|   |   |   |-- orders.py
|   |   |   |-- risk_predict_routes.py
|   |   |   `-- supplier_selection_routes.py
|   |   |-- schemas/
|   |   |   |-- __init__.py
|   |   |   |-- db_models.py
|   |   |   |-- forecast_schema.py
|   |   |   |-- risk_predict_schema.py
|   |   |   `-- supplier_selection_schema.py
|   |   |-- services/
|   |   |   |-- __init__.py
|   |   |   |-- dashboard_dataset.py
|   |   |   |-- dashboard_service.py
|   |   |   |-- forecast_service.py
|   |   |   |-- order_service.py
|   |   |   |-- preprocessing.py
|   |   |   |-- risk_predict_service.py
|   |   |   `-- supplier_selection_service.py
|   |   `-- utils/
|   |       `-- helpers.py
|   |-- database/
|   |   |-- ERD.pgerd
|   |   |-- init.sql
|   |   `-- schema.sql
|   `-- frontend/
|       |-- index.html
|       |-- package.json
|       `-- src/
|           |-- artifact/
|           |   `-- navbar.png
|           |-- css/
|           |   |-- dashboard.css
|           |   |-- landing.css
|           |   |-- product-profiling.css
|           |   |-- shared.css
|           |   `-- supplier-selection.css
|           |-- js/
|           |   |-- api.js
|           |   |-- dashboard.js
|           |   |-- data.js
|           |   |-- main.js
|           |   |-- navbar.js
|           |   |-- product-profiling.js
|           |   `-- pages/
|           |       |-- dashboardPage.js
|           |       |-- product_profilingPage.js
|           |       `-- suplier_selectionPage.js
|           `-- pages/
|               |-- Dashboard.html
|               |-- Product-Profiling.html
|               |-- SupplierSelection.html
|               `-- index.html
`-- model/
    |-- requirements.txt
    |-- artifacts/
    |   |-- models/
    |   |   |-- champion_model/
    |   |   |   |-- late_shipment_model.pkl
    |   |   |   `-- metadata.json
    |   |   `-- forecast/
    |   |       |-- forecast_cat_encoder.pkl
    |   |       |-- forecast_group_stats.json
    |   |       |-- forecast_metadata.json
    |   |       |-- forecast_mkt_encoder.pkl
    |   |       `-- forecast_model.pkl
    |   `-- metrics/
    |       `-- supplier_selection_outputs/
    |           |-- supplier_selection_ahp_weights.csv
    |           |-- supplier_selection_by_category_full_result.csv
    |           |-- supplier_selection_by_category_summary.json
    |           `-- supplier_selection_primary_per_category.csv
    |-- dataset/
    |   |-- processed/
    |   |   `-- .gitkeep
    |   `-- raw/
    |       |-- DataCoSupplyChainDataset.csv
    |       |-- DescriptionDataCoSupplyChain.csv
    |       `-- tokenized_access_logs.csv
    |-- notebooks/
    |   |-- eda/
    |   |   |-- autoEDA.ipynb
    |   |   `-- supplychain_eda.ipynb
    |   |-- feature_engineering/
    |   |   `-- preprocessing_risk.ipynb
    |   |-- modeling/
    |   |   |-- mlops_risk.ipynb
    |   |   |-- mlops_supplier_selection.ipynb
    |   |   `-- mlops_trend.ipynb
    |   `-- pipeline/
    |       `-- pipeline_full.ipynb
    `-- src/
        |-- data/
        |   |-- __init__.py
        |   |-- clean_data.py
        |   |-- load_data.py
        |   `-- split_data.py
        |-- features/
        |   |-- __init__.py
        |   |-- build_features.py
        |   |-- encoding.py
        |   |-- feature_selection.py
        |   `-- preprocessing.py
        |-- inference/
        |   |-- __init__.py
        |   |-- batch_predict.py
        |   `-- predict_late_shipment.py
        |-- training/
        |   |-- __init__.py
        |   |-- evaluate.py
        |   |-- train_late_shipment.py
        |   `-- train_supplier_selection.py
        `-- utils/
            |-- __init__.py
            |-- config.py
            `-- constants.py
```

Generated artifact folders such as MLflow run directories and training logs may contain many additional generated files. They are intentionally not expanded above to keep this stakeholder document readable.

## Main Components

### Frontend

The frontend is a Vite-based static web application.

Important pages:

- `app/frontend/src/pages/index.html`: landing page.
- `app/frontend/src/pages/Dashboard.html`: executive dashboard.
- `app/frontend/src/pages/SupplierSelection.html`: category and product selection.
- `app/frontend/src/pages/Product-Profiling.html`: product trend, forecast, and risk interaction.

Important JavaScript files:

- `app/frontend/src/js/api.js`: API base URL and fetch helpers.
- `app/frontend/src/js/pages/dashboardPage.js`: dashboard API integration and filters.
- `app/frontend/src/js/pages/suplier_selectionPage.js`: supplier category/product selection.
- `app/frontend/src/js/pages/product_profilingPage.js`: product profile, forecast, and risk prediction integration.

### Backend

The backend is a FastAPI application.

Entry point:

```text
app/backend/main.py
```

Runtime command in Docker:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8017
```

Backend responsibilities:

- Serve REST API.
- Connect to PostgreSQL.
- Load ML artifacts.
- Aggregate dashboard data.
- Read supplier ranking CSV/JSON artifacts.
- Prepare forecast and risk model inputs.
- Log risk predictions into PostgreSQL.

### PostgreSQL

PostgreSQL is used for:

- Orders data tables.
- Order item tables.
- Prediction logs.
- Forecast logs.

Initialization script:

```text
app/database/init.sql
```

Host connection:

```text
postgresql://postgres:postgres@localhost:5417/neo_horcrox
```

Docker internal connection:

```text
postgresql+asyncpg://postgres:postgres@postgres:5432/neo_horcrox
```

### Model Artifacts

Risk model:

```text
model/artifacts/models/champion_model/late_shipment_model.pkl
model/artifacts/models/champion_model/metadata.json
```

Forecast model:

```text
model/artifacts/models/forecast/forecast_model.pkl
model/artifacts/models/forecast/forecast_cat_encoder.pkl
model/artifacts/models/forecast/forecast_mkt_encoder.pkl
model/artifacts/models/forecast/forecast_metadata.json
model/artifacts/models/forecast/forecast_group_stats.json
```

Supplier selection:

```text
model/artifacts/metrics/supplier_selection_outputs/supplier_selection_by_category_full_result.csv
model/artifacts/metrics/supplier_selection_outputs/supplier_selection_primary_per_category.csv
model/artifacts/metrics/supplier_selection_outputs/supplier_selection_by_category_summary.json
model/artifacts/metrics/supplier_selection_outputs/supplier_selection_ahp_weights.csv
```

## Data Understanding

Dataset yang digunakan:

| Atribut | Detail |
| --- | --- |
| **Nama** | DataCoSupplyChainDataset.csv |
| **Sumber** | DataCo Smart Supply Chain Dataset (Kaggle / DataCo Global) |
| **Path** | `model/dataset/raw/DataCoSupplyChainDataset.csv` |

Dataset ini mencakup data transaksi order, pengiriman, produk, pelanggan, dan market dari berbagai wilayah global.

Fitur utama yang digunakan:

| Kolom | Deskripsi |
| --- | --- |
| `Type` | Tipe pembayaran (DEBIT, TRANSFER, CASH, dll.) |
| `Days for shipping` | Jumlah hari pengiriman yang direncanakan |
| `Days for shipment` | Jumlah hari aktual pengiriman |
| `Late_delivery_risk` | Label risiko keterlambatan (0 = tepat, 1 = terlambat) |
| `Category Name` | Nama kategori produk |
| `Customer Segment` | Segmen pelanggan (Consumer, Corporate, Home Office) |
| `Market` | Pasar geografis (LATAM, Europe, Pacific Asia, dll.) |
| `Shipping Mode` | Mode pengiriman (Standard, First Class, Second Class, dll.) |
| `Sales` | Total penjualan |
| `Order Profit Per Order` | Profit per order |
| `Product Name` | Nama produk |

## Data Flow

### Dashboard

```text
Dashboard page
  -> GET /api/v1/dashboard/filters
  -> GET /api/v1/dashboard/summary
  -> GET /api/v1/dashboard/risk-by-market
  -> GET /api/v1/dashboard/sales-by-category
  -> GET /api/v1/dashboard/shipping-performance
```

Dashboard data source behavior:

- If PostgreSQL has order data, dashboard reads from PostgreSQL.
- If PostgreSQL is empty, dashboard falls back to `model/dataset/raw/DataCoSupplyChainDataset.csv`.

### Supplier Selection

```text
SupplierSelection.html
  -> GET /api/v1/supplier-selection/categories
  -> User selects category
  -> GET /api/v1/supplier-selection/categories/{category_id}/products
  -> User selects product
  -> GET /api/v1/supplier-selection/products/{candidate_id}
```

Supplier Selection does not run inference. It reads ranking outputs from CSV/JSON artifacts.

### Product Profiling and Forecast

```text
Supplier product detail response
  -> includes forecast_input
  -> frontend stores detail in localStorage
  -> Product-Profiling.html reads localStorage
  -> POST /api/v1/forecast/predict
```

Forecast input example:

```json
{
  "category_name": "Accessories",
  "market": "LATAM",
  "periods": 14,
  "order_year": 2017,
  "order_month": 4
}
```

### Risk Prediction

```text
Product profile/risk action
  -> POST /api/v1/risk/predict
  -> FastAPI builds model features
  -> XGBoost champion model predicts late shipment probability
  -> Result is returned to frontend
  -> Prediction is logged to PostgreSQL
```

## API Reference

The primary API prefix is:

```text
/api/v1
```

Compatibility alias:

```text
/api
```

### Health

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/health` | Check API, database, and artifact status |

### Dashboard

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/dashboard/filters` | Filter options for dashboard sidebar |
| GET | `/api/v1/dashboard/summary` | Executive summary metrics |
| GET | `/api/v1/dashboard/risk-by-market` | Late shipment risk by market |
| GET | `/api/v1/dashboard/sales-by-category` | Sales aggregation by category |
| GET | `/api/v1/dashboard/shipping-performance` | Shipping mode performance |

Supported dashboard query filters:

```text
start_date
end_date
market
order_region
order_country
shipping_mode
category
department
segment
status
risk_level
```

### Supplier Selection

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/supplier-selection/health` | Check supplier ranking artifact availability |
| GET | `/api/v1/supplier-selection/categories` | List product categories |
| GET | `/api/v1/supplier-selection/categories/{category_id}/products` | List ranked products in a category |
| GET | `/api/v1/supplier-selection/products/{candidate_id}` | Product detail, dataset profile, risk input, and forecast input |
| GET | `/api/v1/supplier-selection/summary` | Supplier selection summary |
| GET | `/api/v1/supplier-selection/weights` | AHP criteria weights |

### Forecast

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/forecast/health` | Forecast model health |
| GET | `/api/v1/forecast/options` | Category and market options |
| GET | `/api/v1/forecast/categories` | Forecast category list |
| GET | `/api/v1/forecast/markets` | Forecast market list |
| GET | `/api/v1/forecast/metadata` | Forecast model metadata |
| POST | `/api/v1/forecast/predict` | Demand forecast prediction |

### Risk

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/risk/model` | Risk model metadata |
| POST | `/api/v1/risk/predict` | Single or batch late shipment risk prediction |
| POST | `/api/v1/risk/predict/batch` | Batch risk prediction alias |
| GET | `/api/v1/risk/logs` | Prediction logs from PostgreSQL |

### Orders

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/orders` | List orders with pagination and filters |
| GET | `/api/v1/orders/{order_id}` | Order detail |
| GET | `/api/v1/orders/analytics/risk` | Risk summary from PostgreSQL |
| GET | `/api/v1/orders/analytics/sales` | Sales by category from PostgreSQL |
| POST | `/api/v1/orders` | Insert one order |
| POST | `/api/v1/orders/bulk` | Insert many orders |

## Model Evaluation Results & Project Conclusions

### 1. Late Shipment Risk Prediction Model (Classification)

Dataset: `DataCoSupplyChainDataset.csv` — target label `Late_delivery_risk` (class imbalance ditangani menggunakan Optuna hyperparameter tuning dan regularisasi).

**Perbandingan Algoritma:**

| Model | Accuracy | F1-Score | AUC-ROC | Keterangan |
| --- | --- | --- | --- | --- |
| Decision Tree | 63.23% | 0.6624 | 0.6312 | Baseline |
| Logistic Regression | 69.46% | 0.6579 | 0.7266 | Alternatif Baseline |
| Random Forest | 71.87% | 0.6942 | 0.7573 | — |
| Extra Trees | 71.93% | 0.6945 | 0.7551 | — |
| LightGBM | 71.46% | 0.6943 | 0.7595 | — |
| XGBoost (Default) | 71.46% | 0.6954 | 0.7594 | — |
| CatBoost | 71.93% | 0.6949 | 0.7580 | — |
| **XGBoost (Tuned — Optuna)** | **70.42%** | **0.7025** | **0.7609** | ✓ **Champion Model** |

**Metrik Evaluasi Champion Model pada Validation Set:**

| Metrik | Nilai |
| --- | --- |
| Accuracy | 70.42% |
| Precision (Late Class) | 78.12% |
| Recall (Late Class) | 63.83% |
| F1-Score | 70.25% |
| AUC-ROC | 0.7609 |

**Metrik Evaluasi Final pada Test Set:**

| Metrik | Nilai |
| --- | --- |
| Accuracy | 69.52% |
| Precision (Late Class) | 77.23% |
| Recall (Late Class) | 62.98% |
| F1-Score | 69.38% |
| AUC-ROC | 0.7560 |

XGBoost dipilih sebagai champion model karena memiliki F1-Score dan AUC-ROC tertinggi — dua metrik yang paling penting untuk kasus class imbalance pada deteksi risiko keterlambatan.

### 2. Demand Forecasting Model (Regression)

Model: **XGBoost Regressor** berbasis fitur temporal (lag features, rolling statistics, seasonality).

| Metrik | Nilai |
| --- | --- |
| MAE (Mean Absolute Error) | 127.53 |
| RMSE (Root Mean Squared Error) | 341.10 |
| R² (Coefficient of Determination) | **0.9742 (97.42%)** |

R² sebesar 0.9742 menunjukkan model mampu menjelaskan 97.42% variansi dari demand historis.

### 3. Supplier Selection (Multi-Criteria Decision Making — AHP)

Menggunakan metode **Analytic Hierarchy Process (AHP)**, sistem melakukan pembobotan kriteria secara objektif untuk meranking produk/supplier berdasarkan kombinasi metrik:

- Biaya
- Performa pengiriman
- Profitabilitas
- Tingkat risiko keterlambatan

Output berupa ranking produk per kategori yang disimpan dalam CSV/JSON artifact.

### Kesimpulan Proyek

1. **Sistem End-to-End Terintegrasi**: Project berhasil diintegrasikan secara penuh dari frontend, backend FastAPI, database PostgreSQL, hingga model ML serving dalam satu pipeline orkestrasi kontainer Docker Compose — dapat dijalankan dengan satu perintah: `docker compose up --build`.
2. **Tiga Kapabilitas ML Utama Terimplementasi**:
   - Late Shipment Risk Prediction (XGBoost Champion, AUC-ROC 0.7560)
   - Demand Forecasting (XGBoost Regressor, R² 0.9742)
   - Supplier Selection (AHP multi-criteria ranking)
3. **Pengambilan Keputusan Berbasis Data**: Stakeholder dapat memonitor operasional secara real-time, memilih supplier terbaik secara objektif, serta memitigasi risiko keterlambatan dan merencanakan inventori stok dengan demand forecasting otomatis.
4. **Pipeline MLOps Tersusun**: Siklus hidup ML dari pembersihan data, feature engineering, pelatihan/tuning (Optuna), tracking (notebook-based), penyimpanan artifact, hingga penyajian via REST API telah diselesaikan secara terstruktur.
5. **Arsitektur Skalabel**: Pemisahan layer (frontend, backend, database, model artifacts) memudahkan pengembangan, pemeliharaan, dan scaling di masa depan.

## Setup and Run

### Prerequisites

- Docker Desktop installed and running.
- Git installed.
- Stable internet connection for first build because Python packages and Docker images must be downloaded.

### Run with Docker Compose

From project root:

```powershell
git clone https://github.com/Josshua-DSA/Neo-Horcrox-Project
cd Neo-Horcrox-Project
docker compose up --build
```

Open:

```text
Frontend: http://localhost:5117
API Docs: http://localhost:8017/docs
Health:   http://localhost:8017/api/v1/health
```

### Stop Without Removing Containers

```powershell
docker compose stop
```

Start again:

```powershell
docker compose start
```

### Stop and Remove Containers

This removes containers and Docker network, but keeps PostgreSQL volume data.

```powershell
docker compose down --remove-orphans
```

### Full Database Reset

Only use this if the PostgreSQL data can be deleted.

```powershell
docker compose down -v --remove-orphans
docker compose up --build
```

## Local Backend Run Without Docker

Install dependencies:

```powershell
pip install -r app/requirements.txt
```

Run API:

```powershell
$env:PYTHONPATH="app;."
uvicorn backend.main:app --host 0.0.0.0 --port 8017 --reload
```

API Docs:

```text
http://localhost:8017/docs
```

## Local Frontend Run Without Docker

```powershell
cd app/frontend
npm install
$env:VITE_API_BASE_URL="http://localhost:8017/api/v1"
npm run dev -- --host 0.0.0.0 --port 5117
```

Open:

```text
http://localhost:5117
```

## Environment Configuration

`.env.example` contains the baseline environment values.

Important variables:

| Variable | Default / Example | Purpose |
| --- | --- | --- |
| `APP_NAME` | `Neo Horcrox Supply Chain API` | API display name |
| `APP_VERSION` | `0.1.0` | API version |
| `DEBUG` | `false` | Enables SQLAlchemy echo/debug behavior |
| `LOG_LEVEL` | `INFO` | Logging level |
| `API_PREFIX` | `/api` | Compatibility API prefix |
| `API_V1_PREFIX` | `/api/v1` | Primary API prefix |
| `ALLOWED_ORIGINS` | `*` | CORS origins |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5417/neo_horcrox` | Local PostgreSQL URL outside Docker |
| `MODEL_ROOT` | `./model` | Model and dataset root |
| `CHAMPION_MODEL_PATH` | Optional override | Risk model pickle path |
| `FORECAST_MODEL_DIR` | Optional override | Forecast model artifact directory |
| `SUPPLIER_SELECTION_OUTPUT_DIR` | Optional override | Supplier selection output directory |
| `RAW_SUPPLY_CHAIN_DATASET_PATH` | Optional override | Raw dataset path |

## Current Progress

### Completed

- Project structure separated into `app`, `model`, and `database` layers.
- Docker Compose includes PostgreSQL, API, and frontend services.
- Ports have been moved to avoid common local conflicts:
  - API `8017`
  - Frontend `5117`
  - PostgreSQL host port `5417`
- Backend migrated away from MongoDB runtime paths.
- PostgreSQL connection uses SQLAlchemy async and asyncpg.
- FastAPI routes are aligned under `/api/v1`.
- Compatibility alias `/api` is available.
- Dashboard APIs compute summary, risk, sales, and shipping performance.
- Dashboard filters are available from backend.
- Dashboard can fallback to raw CSV if PostgreSQL order tables are empty.
- Supplier Selection reads ranking artifacts from CSV/JSON.
- Product detail endpoint returns `forecast_input`, `risk_input`, and `dataset_profile`.
- Product Profiling can automatically run forecast based on selected product.
- Risk model loads champion artifact and can predict late shipment risk.
- XGBoost champion model tuned with Optuna (best F1-Score 0.7025, AUC-ROC 0.7609).
- Forecast model (XGBoost Regressor) trained with R² 0.9742.
- Supplier Selection ranking generated using AHP method.
- README and environment documentation are aligned with current ports and architecture.
- Repository pushed to GitHub: https://github.com/Josshua-DSA/Neo-Horcrox-Project

### Verified During Development

- Backend syntax check with `python -m compileall app/backend`.
- Docker Compose configuration validation with `docker compose config --quiet`.
- Supplier Selection service can read category and product detail artifacts.
- Dashboard service can aggregate from CSV fallback.
- Risk model can produce prediction from raw dataset record.
- Frontend JS touched during API alignment passes syntax check.

### Known Warnings

- PostgreSQL Alpine image may show `sh: locale: not found`. This is not fatal.
- Uvicorn logs `0.0.0.0:8017`; open `localhost:8017` in the browser.
- Legacy risk artifacts may be reported as missing. They are optional experiment artifacts, not required for the champion risk model.
- First Docker build can be slow because `xgboost` is a large dependency.

## Current Limitations

- PostgreSQL init creates schema, but does not automatically import the entire raw CSV into orders and order_items.
- Dashboard uses PostgreSQL if populated, otherwise CSV fallback.
- Supplier Selection uses precomputed CSV/JSON ranking, not live model inference.
- Forecast quality depends on the exported artifact and available metadata.
- Frontend is currently a Vite app with static HTML pages and page-level JS.
- Authentication, user roles, and access control are not implemented yet.
- Production deployment hardening is not included yet.

## Future Roadmap

Potential next development stages:

**Jangka Pendek:**

1. Data ingestion pipeline
   - Import raw CSV into PostgreSQL automatically.
   - Add scheduled refresh jobs.
   - Validate schema and data quality before insert.
2. Autentikasi user (JWT) untuk keamanan akses.
3. Unit test dan integration test untuk backend.

**Jangka Menengah:**

4. Production dashboard
   - Persist filter state.
   - Add charts and drill-down views.
   - Add export to PDF/CSV.
5. MLflow integration untuk experiment tracking dan model versioning.
6. SHAP values untuk model interpretability.
7. Batch prediction dan scheduled retraining.
8. Confidence interval pada visualisasi forecast.

**Jangka Panjang:**

9. Supplier decision support
   - Add explainability for ranking criteria.
   - Compare multiple products/suppliers side by side.
   - Add threshold-based recommendation rules.
10. Cloud deployment (GCP, AWS, atau Azure).
11. CI/CD pipeline (GitHub Actions).
12. Model monitoring (data drift detection, performance monitoring).
13. Enterprise readiness: RBAC, observability, alerts.

## Troubleshooting

### Browser Cannot Open `0.0.0.0:8017`

Use:

```text
http://localhost:8017/docs
```

Do not use:

```text
http://0.0.0.0:8017
```

### Port Already in Use

Check running containers:

```powershell
docker compose ps
```

Stop without deleting:

```powershell
docker compose stop
```

Stop and remove containers:

```powershell
docker compose down --remove-orphans
```

### Docker Build Fails While Downloading `xgboost`

`xgboost` is large. Retry:

```powershell
docker compose build api
docker compose up
```

Avoid `--no-cache` unless necessary because Dockerfile uses pip cache layers to reduce repeated downloads.

### API Healthy but Frontend Not Open

Open:

```text
http://localhost:5117
```

Check frontend logs:

```powershell
docker compose logs -f frontend
```

### API Logs Show Missing Legacy Risk Artifacts

This is expected if `model/artifacts/models/risk/` is not present. The active production risk model is:

```text
model/artifacts/models/champion_model/late_shipment_model.pkl
```

## References

### Dataset

- **DataCo SMART Supply Chain Dataset** — DataCo Global
  https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis

### Framework & Library

- FastAPI Documentation: https://fastapi.tiangolo.com/
- XGBoost Documentation: https://xgboost.readthedocs.io/
- LightGBM Documentation: https://lightgbm.readthedocs.io/
- scikit-learn User Guide: https://scikit-learn.org/stable/user_guide.html
- SQLAlchemy AsyncIO: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Docker Documentation: https://docs.docker.com/
- Vite Documentation: https://vitejs.dev/
- PostgreSQL 16 Documentation: https://www.postgresql.org/docs/16/
- Optuna Documentation: https://optuna.readthedocs.io/

### Metode

- Saaty, T. L. (1980). *The Analytic Hierarchy Process*. McGraw-Hill, New York.
- Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. *Proceedings of the 22nd ACM SIGKDD International Conference*. https://doi.org/10.1145/2939672.2939785

### MLOps Referensi

- Sculley, D., et al. (2015). Hidden Technical Debt in Machine Learning Systems. *NIPS 2015*.
- Huyen, Chip (2022). *Designing Machine Learning Systems*. O'Reilly Media.
- MLflow Documentation: https://mlflow.org/docs/latest/index.html

---

## Stakeholder Summary

Neo Horcrox is currently a working local decision-support prototype for supply chain analytics. It already connects frontend, backend, database, dataset artifacts, supplier ranking outputs, risk prediction, and demand forecast into one navigable application.

The current stage is best described as:

```text
Functional local prototype with integrated analytics and ML artifacts.
```

With further development, this project can evolve into:

```text
Operational supply chain intelligence platform with automated ingestion,
model monitoring, decision explainability, and enterprise deployment.
```

---

*Repository: https://github.com/Josshua-DSA/Neo-Horcrox-Project*
