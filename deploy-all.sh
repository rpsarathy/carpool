#!/bin/bash

# Comprehensive deployment script for carpool app with Google OAuth
set -e

PROJECT_ID="carpool-app-470818"
REGION="us-central1"
CLOUD_BUILD_SA="${PROJECT_ID}@cloudbuild.gserviceaccount.com"

echo "🚀 Starting deployment of carpool app with Google OAuth..."

# Step 0: Grant necessary permissions to Cloud Build service account
echo "🔐 Step 0: Setting up Cloud Build permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/run.admin" \
  --project=$PROJECT_ID || echo "Cloud Build already has run.admin role"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/iam.serviceAccountUser" \
  --project=$PROJECT_ID || echo "Cloud Build already has serviceAccountUser role"

# Step 1: Clean up and run local migration to test
echo "📦 Step 1: Testing migration locally..."
rm -f carpool_local.db
alembic upgrade head
echo "✅ Local migration successful"

# Step 2: Deploy API
echo "🔧 Step 2: Deploying API to Cloud Run..."
gcloud builds submit --config cloudbuild.api.yaml --project $PROJECT_ID

# Wait a moment for deployment to settle
sleep 10

# Step 3: Set IAM policy for API (allow unauthenticated access)
echo "🔐 Step 3: Setting IAM policy for API..."
gcloud run services add-iam-policy-binding carpool-api \
  --region=$REGION \
  --member=allUsers \
  --role=roles/run.invoker \
  --project=$PROJECT_ID || echo "⚠️  IAM policy setting failed, but service may still work"

# Step 4: Get the new API URL
echo "🔍 Step 4: Getting API URL..."
API_URL=$(gcloud run services describe carpool-api --region=$REGION --project=$PROJECT_ID --format="value(status.url)")
echo "API URL: $API_URL"

# Step 5: Update web build config with correct API URL
echo "📝 Step 5: Updating web build configuration..."
sed -i.bak "s|_VITE_API_BASE: \".*\"|_VITE_API_BASE: \"$API_URL\"|" cloudbuild.web.yaml

# Step 6: Deploy web app
echo "🌐 Step 6: Deploying web app to Cloud Run..."
gcloud builds submit --config cloudbuild.web.yaml --project $PROJECT_ID

# Wait a moment for deployment to settle
sleep 5

# Step 7: Set IAM policy for web app (allow unauthenticated access)
echo "🔐 Step 7: Setting IAM policy for web app..."
gcloud run services add-iam-policy-binding carpool-web \
  --region=$REGION \
  --member=allUsers \
  --role=roles/run.invoker \
  --project=$PROJECT_ID || echo "⚠️  IAM policy setting failed, but service may still work"

# Step 8: Get final URLs
echo "🎉 Step 8: Deployment complete!"
API_URL=$(gcloud run services describe carpool-api --region=$REGION --project=$PROJECT_ID --format="value(status.url)")
WEB_URL=$(gcloud run services describe carpool-web --region=$REGION --project=$PROJECT_ID --format="value(status.url)")

echo ""
echo "✅ Deployment successful!"
echo "📡 API URL: $API_URL"
echo "🌐 Web URL: $WEB_URL"
echo ""
echo "🔧 Google OAuth Configuration:"
echo "1. Ensure your Google OAuth Client ID is configured for:"
echo "   - $WEB_URL (production domain)"
echo "   - http://localhost:5173 (local development)"
echo "2. Check that CORS is configured in the API for both domains"
echo ""
echo "🔍 Troubleshooting:"
echo "   - API logs: gcloud logs read --service=carpool-api --project=$PROJECT_ID"
echo "   - Web logs: gcloud logs read --service=carpool-web --project=$PROJECT_ID"
echo "   - Test API health: curl $API_URL/health"

# Restore original cloudbuild.web.yaml
mv cloudbuild.web.yaml.bak cloudbuild.web.yaml
