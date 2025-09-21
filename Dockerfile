# --------------------------
# Base image
# --------------------------
FROM python:3.12-slim

# --------------------------
# Set working directory
# --------------------------
WORKDIR /app


# --------------------------
# Copy & install Python dependencies
# --------------------------
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
    
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --------------------------
# Copy project files
# --------------------------
COPY . .
# Collect static safely
# --------------------------
RUN python manage.py collectstatic --noinput || echo "Warning: collectstatic skipped"

# --------------------------
# Expose port
# --------------------------
EXPOSE 8000

# --------------------------
# Run Django dev server (replace with gunicorn in prod)
# --------------------------
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
