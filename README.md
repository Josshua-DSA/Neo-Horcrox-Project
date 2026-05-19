=======
# Supply Chain Analytics

Project TA untuk analitik supply chain:

1. Late delivery risk prediction
2. Demand forecasting
3. Supplier selection ranking
4. Dashboard analytics

## Struktur Project

```text
Project TA/
|-- app/
|   |-- backend/
|   |   |-- core/       # MongoDB connection dan ModelRegistry
|   |   |-- routes/     # FastAPI routers
|   |   |-- schemas/    # Pydantic schemas
|   |   |-- services/   # Business logic
|   |   `-- main.py     # FastAPI entry point
|   |-- frontend/       # Vite frontend
|   `-- database/       # SQL/ERD references
|-- model/
|   |-- artifacts/
|   |   |-- models/champion_model/   # production risk model
|   |   |-- models/forecast/         # forecast model artifacts
|   |   |-- models/risk/             # legacy/experiment risk candidate
|   |   `-- metrics/supplier_selection_outputs/
|   `-- dataset/
|-- Dockerfile
`-- docker-compose.yaml
```

## Backend

Install dependency:

```bash
pip install -r app/requirements.txt
```

<<<<<<< HEAD
Server default berjalan di `http://localhost:5000`.

### Endpoint

- `GET /api/health` cek status service dan model.
- `GET /api/model` lihat metadata model, fitur, target, dan threshold.
- `POST /api/predict/late-shipment` prediksi late delivery risk untuk satu record atau banyak record.
- `POST /api/predict` alias endpoint prediksi.
- `GET /api/supplier-selection/categories` daftar kategori supplier selection.
- `GET /api/supplier-selection/categories/<category_id>/products` ranking product/candidate teratas per kategori.
- `GET /api/supplier-selection/products/<candidate_id>` profile product/candidate dari metrics CSV.
- `GET /api/supplier-selection/summary` ringkasan supplier selection.
- `GET /api/supplier-selection/weights` bobot AHP supplier selection.

### Contoh Request

```bash
curl -X POST http://localhost:5000/api/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"Latitude\":18.25,\"Longitude\":-66.37,\"order_date\":\"2018-01-31 22:56:00\",\"shipping_mode\":\"Standard Class\"}"
```

Input boleh memakai fitur final langsung dari `metadata.json`, atau field raw `order_date`, `Longitude`, dan `shipping_mode`; backend akan menurunkan `geo_distance_proxy`, `order_hour`, `order_period`, `scheduled_days`, `scheduled_by_mode`, `expected_scheduled_days_by_mode`, `is_first_class_mode`, `is_second_class_mode`, dan `is_medium_shipping` otomatis.

Mapping shipping mode:

- `Same Day` -> `0` hari
- `First Class` -> `1` hari
- `Second Class` -> `2` hari
- `Standard Class` -> `4` hari

Run API:

```bash
uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Docs:

```text
http://localhost:8000/docs
```

## Docker

```bash
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- MongoDB: `localhost:27017`

## API Utama

Health:

- `GET /api/health`

Risk:

- `GET /api/risk/model`
- `POST /api/risk/predict`
- Alias v1 juga tersedia: `/api/v1/risk/...`

Forecast:

- `GET /api/forecast/health`
- `GET /api/forecast/categories`
- `GET /api/forecast/markets`
- `POST /api/forecast/predict`

Supplier Selection:

- `GET /api/supplier-selection/health`
- `GET /api/supplier-selection/categories`
- `GET /api/supplier-selection/categories/{category_id}/products`
- `GET /api/supplier-selection/products/{candidate_id}`
- `GET /api/supplier-selection/summary`
- `GET /api/supplier-selection/weights`

Dashboard:

- `GET /api/dashboard/summary`
- `GET /api/dashboard/risk-by-market`
- `GET /api/dashboard/sales-by-category`
- `GET /api/dashboard/shipping-performance`

## Artifact Policy

- Risk production memakai `model/artifacts/models/champion_model/late_shipment_model.pkl`.
- Metadata production ada di `model/artifacts/models/champion_model/metadata.json`.
- Folder `model/artifacts/models/risk/` tetap disimpan sebagai kandidat lama/eksperimen.
- Supplier Selection tidak memakai model inference. Backend membaca ranking dari CSV/JSON di `model/artifacts/metrics/supplier_selection_outputs/`.

## Environment

Lihat `.env.example` untuk override path artifact, dataset, CORS, dan MongoDB.
