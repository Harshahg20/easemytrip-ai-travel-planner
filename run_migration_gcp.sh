#!/bin/bash
# Script to run database migration on Google Cloud SQL
set -e

# Configuration
PROJECT="gen-ai-hackathon-476317"
REGION="us-central1"
SQL_INSTANCE="tripplanner-mysql"
DB_NAME="tripdb"
DB_USER="appuser"

echo "=================================================="
echo "Running Database Migration on Google Cloud SQL"
echo "=================================================="
echo ""

# Get the database password from Secret Manager
echo "📦 Fetching database password from Secret Manager..."
DB_PASSWORD=$(gcloud secrets versions access latest --secret=DB_PASSWORD --project=$PROJECT)

# Get Cloud SQL connection name
echo "🔍 Getting Cloud SQL connection name..."
CLOUD_SQL_CONNECTION_NAME=$(gcloud sql instances describe $SQL_INSTANCE --project=$PROJECT --format='value(connectionName)')
echo "   Connection: $CLOUD_SQL_CONNECTION_NAME"
echo ""

# Construct database URL
DATABASE_URL="mysql+pymysql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?unix_socket=/cloudsql/${CLOUD_SQL_CONNECTION_NAME}"

echo "🚀 Running migration..."
echo ""

# Run migration in Cloud Run environment using gcloud run jobs
# First, check if the job exists
if gcloud run jobs describe migration-job --region=$REGION --project=$PROJECT &>/dev/null; then
    echo "⚠️  Migration job already exists, deleting it..."
    gcloud run jobs delete migration-job --region=$REGION --project=$PROJECT --quiet
fi

# Create a temporary Cloud Run job to run the migration
echo "📦 Creating Cloud Run job for migration..."
gcloud run jobs create migration-job \
    --image=$REGION-docker.pkg.dev/$PROJECT/tripplanner/backend:prod \
    --region=$REGION \
    --project=$PROJECT \
    --service-account=cloudrun-app@$PROJECT.iam.gserviceaccount.com \
    --set-cloudsql-instances="$CLOUD_SQL_CONNECTION_NAME" \
    --set-env-vars="DATABASE_URL=${DATABASE_URL}" \
    --task-timeout=5m \
    --max-retries=0 \
    --command=python \
    --args="migrate_add_users.py"

echo ""
echo "🎯 Executing migration job..."
gcloud run jobs execute migration-job \
    --region=$REGION \
    --project=$PROJECT \
    --wait

echo ""
echo "✅ Migration completed!"
echo ""
echo "🧹 Cleaning up migration job..."
gcloud run jobs delete migration-job --region=$REGION --project=$PROJECT --quiet

echo ""
echo "=================================================="
echo "✅ Migration completed successfully!"
echo "=================================================="

