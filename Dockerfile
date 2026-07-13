FROM python:3.9-slim

# Set working directorys
WORKDIR /app

# Install system dependencies required for mysqlclient (Flask-MySQLdb)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better for Docker caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Run Flask app
CMD ["python", "app.py"]


