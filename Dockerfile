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

# --------------------------
# Copy & install Python dependencies
# --------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --------------------------
# Copy project files
# --------------------------
COPY . .

# --------------------------
# Default environment variables to prevent missing .env issues
# Can be overridden by real .env or docker-compose env_file
# --------------------------
ENV DEBUG=False
ENV SECRET_KEY=fallback-secret-for-dev-only
ENV DATABASE_URL=sqlite:///:memory:

# --------------------------
# Collect static files safely
# --------------------------
RUN python -c "\
import os; \
os.environ.setdefault('SECRET_KEY', 'fallback-secret-for-dev-only'); \
os.environ.setdefault('DEBUG', 'False'); \
try: \
    from django.core.management import execute_from_command_line; \
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput']); \
except Exception as e: \
    print('Warning: collectstatic skipped', e)\
"

# --------------------------
# Expose port
# --------------------------
EXPOSE 8000

# --------------------------
# Run Django dev server (replace with gunicorn in prod)
# --------------------------
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
