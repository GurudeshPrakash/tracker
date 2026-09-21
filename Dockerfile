# Stage 1: Build TypeScript Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY db/ ./db/
COPY lib/ ./lib/
COPY services/ ./services/
COPY pages/ ./pages/
COPY reminders/ ./reminders/
COPY app.py server.py ./

# Copy built frontend assets
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create persistent data and backup directories
RUN mkdir -p /app/data /app/backups

# Expose port
EXPOSE 8501

# Entrypoint script to handle dynamic $PORT and run server
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8501}"]
