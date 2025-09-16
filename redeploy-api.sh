#!/bin/bash
set -e

echo "🔧 Redeploying API with fixes..."

# Set project
gcloud config set project carpool-app-470818

# Deploy API only
echo "Building and deploying API..."
gcloud builds submit --config cloudbuild.api.yaml .

# Test the deployment
echo "Testing API deployment..."
API_URL="https://carpool-api-dzxkfcfuiq-uc.a.run.app"

sleep 10  # Give it a moment to start

if curl -s -f "${API_URL}/health" > /dev/null; then
    echo "✅ API deployment successful!"
    echo "📍 API URL: ${API_URL}"
    echo "📍 Health: ${API_URL}/health"
    echo "📍 Docs: ${API_URL}/docs"
else
    echo "⚠️  API may still be starting up. Check logs:"
    echo "   gcloud logs tail --service=carpool-api"
fi
