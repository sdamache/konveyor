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

# Copy all requirements files
COPY requirements/*.txt /app/requirements/

# Install Python dependencies into a wheelhouse for faster installation in the final stage
# Install all requirements for testing and development
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements/testing.txt


# Stage 2: Final - Build the final application image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Accept build argument for settings module with a default
ARG DJANGO_SETTINGS_MODULE=konveyor.settings.testing
ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}

# Set working directory
WORKDIR /app

# Install system dependencies needed only at runtime (e.g., libpq5 for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from the builder stage's wheelhouse
COPY --from=builder /wheels /wheels
# Copy all requirements files
COPY --from=builder /app/requirements/*.txt /app/requirements/
# Install wheels from the wheelhouse
RUN pip install --no-cache /wheels/*

# Create a non-root user and group for security
RUN addgroup --system app && adduser --system --group app

# Copy the application code into the container
# This respects the .dockerignore file
COPY . /app/

# Set ownership of the app directory to the non-root user
RUN chown -R app:app /app

# Create logs, static, and test results directories to prevent FileNotFoundError during startup
RUN mkdir -p /app/logs /app/static /app/staticfiles /app/tests/results && \
    chown -R app:app /app/logs /app/static /app/staticfiles /app/tests/results && \
    chmod -R 777 /app/tests/results

# Create a script to run collectstatic at container startup
RUN echo '#!/bin/bash\n\
if [ "$SKIP_COLLECTSTATIC" != "true" ]; then\n\
  python manage.py collectstatic --noinput --settings=$DJANGO_SETTINGS_MODULE || true\n\
fi\n\
exec "$@"' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Switch to the non-root user
USER app

# Expose the port Gunicorn will run on (default is 8000)
EXPOSE 8000

# Set the entrypoint to our script that handles collectstatic
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command runs gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "konveyor.wsgi:application"]