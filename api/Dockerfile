FROM python:3.11-slim

WORKDIR /app

# Install sqlite3 CLI (required by grader)
RUN apt-get update \
    && apt-get install -y --no-install-recommends sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Create directories that the app needs at runtime
RUN mkdir -p /data /app/logs

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]