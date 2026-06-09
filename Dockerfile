FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh source code backend
COPY app/backend /app/backend

# Copy KESELURUHAN folder model (termasuk artifacts dan src)
COPY model /app/model

EXPOSE 8017

# Jalankan Uvicorn dengan port 8017
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8017"]