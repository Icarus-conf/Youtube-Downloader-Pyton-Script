FROM python:3.11-slim

# Install system dependencies (ffmpeg is required)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application code
COPY . .

# Create downloads directory and set permissions
RUN mkdir -p downloads && chmod 777 downloads

# Expose the port
EXPOSE 5001

# Run the application
# Using threading mode as configured in app.py
CMD ["gunicorn", "--worker-class", "gthread", "--threads", "4", "--bind", "0.0.0.0:5001", "app:app"]
