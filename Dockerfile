FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    DB_PATH=/app/state/property_energy.sqlite3

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/state /app/data
EXPOSE 8000
# Recreates the deterministic, fictional demonstration data at every start.
CMD ["sh", "-c", "python ingest.py --generate && exec uvicorn main:app --host 0.0.0.0 --port 8000"]
