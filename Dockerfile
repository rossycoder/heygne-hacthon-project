FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Set working directory to backend so relative imports work
WORKDIR /app/backend

# Expose port 7860 (HuggingFace Spaces default)
EXPOSE 7860

# Run uvicorn from inside backend folder
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
