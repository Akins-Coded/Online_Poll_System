# --------------------------
# Base image
# --------------------------
FROM python:3.11-slim

# --------------------------
# Set working directory
# --------------------------
WORKDIR /app

# --------------------------
# Install system dependencies
# --------------------------
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# --------------------------
# Prevent .pyc creation & unbuffered logs
# --------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


# Set default environment variables
# --------------------------
ENV DEBUG=False
ENV SECRET_KEY=fallback-secret-for-dev-only
ENV DATABASE_URL=sqlite:///:memory:

# --------------------------
# Copy & install Python dependencies
# --------------------------
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
