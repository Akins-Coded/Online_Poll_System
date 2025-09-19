# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system deps (Postgres, build tools)
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Prevent .pyc creation and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files (inside container)
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Production command → still using Django dev server (⚠️ not recommended for big load)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
