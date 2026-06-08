# syntax=docker/dockerfile:1.7 
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/requirements.txt ./requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --index-url https://pypi.org/simple --prefer-binary --retries 20 --timeout 300 --progress-bar off xgboost==3.2.0
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --index-url https://pypi.org/simple --prefer-binary --retries 10 --timeout 300 --progress-bar off -r requirements.txt

COPY app/__init__.py ./app/__init__.py
COPY app/backend ./app/backend
COPY model ./model

# --- PERUBAHAN UNTUK HUGGING FACE ---
# Buat user non-root dan berikan izin ke folder /app jika aplikasi Anda menulis file di sana
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

ENV PYTHONPATH=/app/app:/app
WORKDIR /app/app

# Ganti port dari 8017 menjadi 7860
EXPOSE 7860

# Sesuaikan port uvicorn ke 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]