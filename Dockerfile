# Backend API image (Render / any container host). Light: no torch.
FROM python:3.12-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

ENV PORT=8000
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT
