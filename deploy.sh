#!/bin/bash
set -e

PROJECT=gen-ai-hackathon-476317
REGION=us-central1
REPO=tripplanner
RUN_SVC=tripplanner-backend
FRONTEND_SVC=tripplanner-frontend
SQL_INSTANCE=tripplanner-mysql
DB=tripdb
DB_USER=appuser

echo "🚀 Starting deployment..."

# Get secrets (you'll need to set these)
read -sp "Enter DB Password (or press Enter to generate new): " DB_PASS
if [ -z "$DB_PASS" ]; then
    DB_PASS=$(openssl rand -base64 24)
    gcloud sql users set-password $DB_USER --instance=$SQL_INSTANCE --password="$DB_PASS"
fi

read -sp "Enter GOOGLE_AI_API_KEY: " GOOGLE_AI_KEY
read -sp "Enter GOOGLE_MAPS_API_KEY: " GOOGLE_MAPS_KEY
read -sp "Enter SECRET_KEY: " SECRET_KEY

echo ""
echo "📦 Creating secrets..."

# Create/update secrets
echo -n "$DB_PASS" | gcloud secrets create DB_PASSWORD --data-file=- 2>/dev/null || \
    echo -n "$DB_PASS" | gcloud secrets versions add DB_PASSWORD --data-file=-

echo -n "$GOOGLE_AI_KEY" | gcloud secrets create GOOGLE_AI_API_KEY --data-file=- 2>/dev/null || \
    echo -n "$GOOGLE_AI_KEY" | gcloud secrets versions add GOOGLE_AI_API_KEY --data-file=-

echo -n "$GOOGLE_MAPS_KEY" | gcloud secrets create GOOGLE_MAPS_API_KEY --data-file=- 2>/dev/null || \
    echo -n "$GOOGLE_MAPS_KEY" | gcloud secrets versions add GOOGLE_MAPS_API_KEY --data-file=-

echo -n "$SECRET_KEY" | gcloud secrets create SECRET_KEY --data-file=- 2>/dev/null || \
    echo -n "$SECRET_KEY" | gcloud secrets versions add SECRET_KEY --data-file=-

echo "✅ Secrets created"

# Service account
echo "👤 Setting up service account..."
gcloud iam service-accounts create cloudrun-app --display-name="Cloud Run Runtime" 2>/dev/null || true
SA="cloudrun-app@$PROJECT.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT --member="serviceAccount:$SA" --role="roles/cloudsql.client" 2>/dev/null || true
gcloud projects add-iam-policy-binding $PROJECT --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor" 2>/dev/null || true
gcloud projects add-iam-policy-binding $PROJECT --member="serviceAccount:$SA" --role="roles/artifactregistry.reader" 2>/dev/null || true

# Get SQL connection
ICN=$(gcloud sql instances describe $SQL_INSTANCE --format='value(connectionName)')
echo "🔌 SQL Connection: $ICN"

# Deploy backend
echo "🚀 Deploying backend..."
gcloud run deploy $RUN_SVC \
  --image=$REGION-docker.pkg.dev/$PROJECT/$REPO/backend:prod \
  --region=$REGION --platform=managed \
  --service-account=$SA \
  --add-cloudsql-instances="$ICN" \
  --update-env-vars="DATABASE_URL=mysql+pymysql://$DB_USER:\$(DB_PASSWORD)/$DB?unix_socket=/cloudsql/$ICN,GOOGLE_CLOUD_PROJECT_ID=$PROJECT,GOOGLE_CLOUD_REGION=$REGION,ENVIRONMENT=production,DEBUG=False" \
  --set-secrets="DB_PASSWORD=DB_PASSWORD:latest,GOOGLE_AI_API_KEY=GOOGLE_AI_API_KEY:latest,GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY:latest,SECRET_KEY=SECRET_KEY:latest" \
  --allow-unauthenticated \
  --min-instances=0 --max-instances=5 --cpu=1 --memory=512Mi --concurrency=80 --port=8000

BACKEND_URL=$(gcloud run services describe $RUN_SVC --region=$REGION --format='value(status.url)')
echo "✅ Backend deployed: $BACKEND_URL"

# Build and deploy frontend
echo "🎨 Building frontend..."
cd frontend
REACT_APP_API_URL="$BACKEND_URL/api/v1" npm run build

echo "📦 Building frontend Docker image..."
docker build -t $REGION-docker.pkg.dev/$PROJECT/$REPO/frontend:prod \
  --build-arg REACT_APP_API_URL="$BACKEND_URL/api/v1" .

echo "⬆️ Pushing frontend image..."
docker push $REGION-docker.pkg.dev/$PROJECT/$REPO/frontend:prod

echo "🚀 Deploying frontend..."
gcloud run deploy $FRONTEND_SVC \
  --image=$REGION-docker.pkg.dev/$PROJECT/$REPO/frontend:prod \
  --region=$REGION \
  --allow-unauthenticated \
  --min-instances=0 --max-instances=3 --cpu=1 --memory=256Mi --port=80

FRONTEND_URL=$(gcloud run services describe $FRONTEND_SVC --region=$REGION --format='value(status.url)')
echo "✅ Frontend deployed: $FRONTEND_URL"

# Update backend CORS
echo "🔧 Updating backend CORS..."
gcloud run services update $RUN_SVC \
  --region=$REGION \
  --update-env-vars="ALLOWED_ORIGINS=$FRONTEND_URL,http://localhost:3000"

cd ..
echo ""
echo "🎉 Deployment complete!"
echo "Backend:  $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"

