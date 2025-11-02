#!/bin/bash
set -e

# Cloud Run provides PORT env var - use it or default to 8000
export PORT=${PORT:-8000}

# Construct DATABASE_URL from individual components if not set
if [ -z "$DATABASE_URL" ]; then
    # Read from environment variables set by Cloud Run secrets
    if [ -n "$DB_PASSWORD" ] && [ -n "$DB_USER" ] && [ -n "$DB_NAME" ] && [ -n "$CLOUD_SQL_CONNECTION_NAME" ]; then
        export DATABASE_URL="mysql+pymysql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?unix_socket=/cloudsql/${CLOUD_SQL_CONNECTION_NAME}"
    fi
fi

# Run the application
exec python run.py
