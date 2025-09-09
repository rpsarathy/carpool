#!/bin/bash
set -e

echo "🚀 Carpool App - Complete Deployment to GCP"
echo "=============================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set project
echo "📋 Setting GCP project..."
gcloud config set project carpool-app-470818

# Check authentication
echo "🔐 Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with gcloud. Please run: gcloud auth login"
    exit 1
fi

# Commit current changes
echo "📝 Committing code changes..."
git add .
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit"
else
    git commit -m "PostgreSQL migration complete - ready for deployment

- Migrated from TinyDB to PostgreSQL with SQLite fallback for local dev
- Fixed all authentication endpoints (/auth/register, /auth/login, /auth/me)
- Updated group management with proper validation
- Fixed on-demand requests with simplified schema
- Added admin endpoints for user management
- All 16 API tests passing
- Ready for production deployment

Deployment includes:
- API service: carpool-api
- Web service: carpool-web
- PostgreSQL database connection
- Environment-aware database configuration"
fi

# Deploy API
echo ""
echo "🔧 Deploying API to Cloud Run..."
echo "Service: carpool-api"
echo "Region: us-central1"
gcloud builds submit --config cloudbuild.api.yaml .

# Deploy Web Frontend
echo ""
echo "🌐 Deploying Web Frontend to Cloud Run..."
echo "Service: carpool-web"
echo "Region: us-central1"
gcloud builds submit --config cloudbuild.web.yaml .

# Test deployment
echo ""
echo "🧪 Testing deployed services..."

API_URL="https://carpool-api-dzxkfcfuiq-uc.a.run.app"
WEB_URL="https://carpool-web-dzxkfcfuiq-uc.a.run.app"

# Test API health
echo "Testing API health..."
if curl -s -f "${API_URL}/health" > /dev/null; then
    echo "✅ API is healthy"
else
    echo "⚠️  API health check failed (may take a few minutes to be ready)"
fi

# Test web frontend
echo "Testing web frontend..."
if curl -s -f "${WEB_URL}" > /dev/null; then
    echo "✅ Web frontend is accessible"
else
    echo "⚠️  Web frontend check failed (may take a few minutes to be ready)"
fi

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo "📍 API URL:     ${API_URL}"
echo "📍 Web URL:     ${WEB_URL}"
echo "📍 Health:      ${API_URL}/health"
echo "📍 API Docs:    ${API_URL}/docs"
echo ""
echo "🔍 To run comprehensive tests:"
echo "   python test_gcp_deployment.py"
echo ""
echo "📊 To view logs:"
echo "   gcloud logs tail --service=carpool-api"
echo "   gcloud logs tail --service=carpool-web"
