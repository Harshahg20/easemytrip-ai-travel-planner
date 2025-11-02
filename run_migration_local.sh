#!/bin/bash
# Script to run database migration using Cloud SQL Proxy locally
set -e

# Configuration
PROJECT="gen-ai-hackathon-476317"
SQL_INSTANCE="tripplanner-mysql"
DB_NAME="tripdb"
DB_USER="appuser"

echo "=================================================="
echo "Running Database Migration via Cloud SQL Proxy"
echo "=================================================="
echo ""

# Add local bin to PATH
export PATH="$HOME/.local/bin:$PATH"

# Check if cloud_sql_proxy is installed
if ! command -v cloud-sql-proxy &> /dev/null; then
    echo "❌ cloud-sql-proxy not found!"
    echo ""
    echo "Install it with:"
    echo "  curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64"
    echo "  chmod +x cloud-sql-proxy"
    echo "  mkdir -p ~/.local/bin && mv cloud-sql-proxy ~/.local/bin/"
    echo ""
    exit 1
fi

# Get the database password from Secret Manager
echo "📦 Fetching database password from Secret Manager..."
DB_PASSWORD=$(gcloud secrets versions access latest --secret=DB_PASSWORD --project=$PROJECT)

# Get Cloud SQL connection name
echo "🔍 Getting Cloud SQL connection name..."
CLOUD_SQL_CONNECTION_NAME=$(gcloud sql instances describe $SQL_INSTANCE --project=$PROJECT --format='value(connectionName)')
echo "   Connection: $CLOUD_SQL_CONNECTION_NAME"
echo ""

# Start Cloud SQL Proxy in background
echo "🚀 Starting Cloud SQL Proxy..."
cloud-sql-proxy --port 3307 $CLOUD_SQL_CONNECTION_NAME &
PROXY_PID=$!
echo "   Proxy PID: $PROXY_PID"

# Wait for proxy to be ready
echo "⏳ Waiting for proxy to be ready..."
sleep 3

# Construct database URL for localhost
DATABASE_URL="mysql+pymysql://${DB_USER}:${DB_PASSWORD}@127.0.0.1:3307/${DB_NAME}"

echo ""
echo "🔧 Running migration..."
echo ""

# Run migration
cd backend
export DATABASE_URL=$DATABASE_URL
python3 migrate_add_users.py

# Kill the proxy
echo ""
echo "🧹 Stopping Cloud SQL Proxy..."
kill $PROXY_PID 2>/dev/null || true

echo ""
echo "=================================================="
echo "✅ Migration completed successfully!"
echo "=================================================="

