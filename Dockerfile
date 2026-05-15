FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend files directly
COPY backend/app.py .
COPY backend/ai_client.py .
COPY backend/heygen_client.py .
COPY backend/news_fetcher.py .
COPY backend/script_generator.py .
COPY backend/live_news.py .
COPY backend/broadcast_history.py .

# Copy .env if exists (for local docker testing)
COPY .env.example .env.example

# Expose port 7860 (HuggingFace Spaces default)
EXPOSE 7860

# Run uvicorn directly from /app where all .py files are
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
