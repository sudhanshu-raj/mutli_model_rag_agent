# Base image - use Python 3.11 with Debian Bookworm which has newer SQLite
FROM python:3.11-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies including MySQL client and SQLite
RUN apt-get update && apt-get install -y --no-install-recommends \
    ghostscript \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    gcc \
    g++ \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    sqlite3 \
    poppler-utils \  
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify SQLite version meets requirements
RUN sqlite3 --version

# Copy requirements.txt first for better cache utilization
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir git+https://github.com/openai/CLIP.git@dcba3cb2e2827b402d2701e7e1c7d9fed8a20ef1 \
    && pip install --no-cache-dir mysqlclient pymysql

# Create necessary directories
RUN mkdir -p /app/media/files-metadata \
    /app/media/images \
    /app/media/chroma-data \
    /app/media/output \
    /app/uploaded_files \
    /app/logs

# Copy source code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "src/flaskAPI/index.py"]