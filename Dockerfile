# Stage 1: Builder - Install dependencies
FROM python:3.10-slim as builder

# Set environment variables to prevent caching and ensure output is sent directly
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install system dependencies required for building psycopg2 and potentially others
# Using --no-install-recommends keeps the layer smaller
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Copy only the necessary requirements files for production
COPY requirements/base.txt requirements/production.txt /app/requirements/

# Install Python dependencies into a wheelhouse for faster installation in the final stage
# Use production.txt which includes base.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements/production.txt


# Stage 2: Final - Build the final application image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=konveyor.settings.production

# Set working directory
WORKDIR /app

# Install system dependencies needed only at runtime (e.g., libpq5 for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from the builder stage's wheelhouse
COPY --from=builder /wheels /wheels
# Copy the production requirements file again to ensure pip knows what was installed
COPY --from=builder /app/requirements/production.txt .
# Install wheels from the wheelhouse
RUN pip install --no-cache /wheels/*

# Create a non-root user and group for security
RUN addgroup --system app && adduser --system --group app

# Copy the application code into the container
# This respects the .dockerignore file
COPY . /app/

# Set ownership of the app directory to the non-root user
RUN chown -R app:app /app

# Collect static files using Django's collectstatic command
# Run as root first to ensure permissions to write to STATIC_ROOT defined in settings
RUN python manage.py collectstatic --noinput --settings=$DJANGO_SETTINGS_MODULE

# Switch to the non-root user
USER app

# Expose the port Gunicorn will run on (default is 8000)
EXPOSE 8000

# Run the application using Gunicorn WSGI server
# Use environment variables for host/port if needed, default is 0.0.0.0:8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "konveyor.wsgi:application"]