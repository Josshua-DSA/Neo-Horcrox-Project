FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh source code backend & artifacts model
COPY app/app /app/backend
COPY model/artifacts /app/model/artifacts

EXPOSE 8017

# Jalankan Uvicorn dengan port 8017 (port default proyek kelompokmu)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8017"]