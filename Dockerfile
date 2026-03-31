FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Run data collection on first start, then start the server
# Railway provides $PORT; fall back to 8000 for local compatibility
CMD ["sh", "-c", "python data_collector.py && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
