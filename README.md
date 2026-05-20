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
