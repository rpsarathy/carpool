# carpool

A modern Python project scaffold using the src/ layout.

## Features
- src/ layout for import safety
- pyproject.toml (PEP 621 with setuptools)
- Simple CLI (`python -m carpool` or `carpool` after install)
- pytest test suite

## Quickstart

1) Create and activate a virtual environment

   macOS/Linux:
   python3 -m venv .venv
   source .venv/bin/activate

   Windows (PowerShell):
   py -m venv .venv
   .venv\Scripts\Activate.ps1

2) Install the project in editable mode with dev tools

   pip install -U pip
   pip install -e '.[dev]'

3) Run the tests

   pytest -q

4) Use the CLI

   carpool --help
   # or without installing
   python -m carpool --help

## Project Structure

c  carpool/
├─ .gitignore
├─ pyproject.toml
├─ README.md
├─ pytest.ini
├─ src/
│  └─ carpool/
│     ├─ __init__.py
│     ├─ __main__.py
│     └─ cli.py
└─ tests/
   └─ test_sanity.py

## Releasing (optional)
- Build: `python -m build`
- Publish: `python -m twine upload dist/*`

## Deploy to Google Cloud Run

This project has two services:
- API (FastAPI) — Dockerfile: `Dockerfile.api`, listens on port 8000
- Web (Vite + React) — Dockerfile: `web/Dockerfile.web`, served by nginx on port 8080

TinyDB stores data in `data/db.json`. Cloud Run instances are ephemeral; treat this as non-persistent. For persistence, migrate to a managed DB (e.g., Firestore/Cloud SQL) in the future.

### Prerequisites
- gcloud CLI installed and authenticated
- A Google Cloud project set and billing enabled
- APIs enabled: Cloud Run, Artifact Registry (or Container Registry), Cloud Build (optional)

```bash
PROJECT_ID=your-project-id
REGION=us-central1
API_SERVICE=carpool-api
WEB_SERVICE=carpool-web
API_IMAGE=gcr.io/$PROJECT_ID/$API_SERVICE
WEB_IMAGE=gcr.io/$PROJECT_ID/$WEB_SERVICE
```

### Option A: Build with local Docker, push, and deploy

1) Build and push the API image
```bash
docker build -f Dockerfile.api -t $API_IMAGE .
docker push $API_IMAGE
```

2) Deploy the API to Cloud Run
```bash
gcloud run deploy $API_SERVICE \
  --image $API_IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8000
# Capture the URL printed by Cloud Run, e.g., https://carpool-api-xxxxx-uc.a.run.app
API_URL=https://<your-api-url>
```

3) Build and push the Web image (bake API base URL)
```bash
# VITE_API_BASE is compiled into the bundle at build time
docker build -f web/Dockerfile.web -t $WEB_IMAGE --build-arg VITE_API_BASE=$API_URL .
docker push $WEB_IMAGE
```

4) Deploy the Web to Cloud Run
```bash
gcloud run deploy $WEB_SERVICE \
  --image $WEB_IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080
```

### Option B: Use Cloud Build (gcloud builds submit)

1) API via Cloud Build
```bash
gcloud builds submit --tag $API_IMAGE --file Dockerfile.api .
gcloud run deploy $API_SERVICE \
  --image $API_IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8000
API_URL=https://<your-api-url>
```

2) Web with Cloud Build
Cloud Build does not pass `--build-arg` via `gcloud builds submit` directly. Either:
- Build locally as in Option A step 3, or
- Create a Cloud Build config to pass build args. Example `cloudbuild.web.yaml`:

```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-f', 'web/Dockerfile.web', '-t', '$WEB_IMAGE', '--build-arg', 'VITE_API_BASE=$API_URL', '.']
images: ['$WEB_IMAGE']
substitutions:
  _API_URL: ""
```
Run:
```bash
API_URL=https://<your-api-url>
gcloud builds submit --config cloudbuild.web.yaml --substitutions WEB_IMAGE=$WEB_IMAGE,_API_URL=$API_URL .
gcloud run deploy $WEB_SERVICE \
  --image $WEB_IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080
```

### CORS
The API currently allows all origins (`*`) via CORS in `src/carpool/api.py`. For stricter security, set `allow_origins` to your Web service URL after deployment.

### Local testing with Docker
```bash
# API
docker run --rm -p 8000:8000 $API_IMAGE
# Web (served at http://localhost:8080)
docker run --rm -p 8080:8080 $WEB_IMAGE
```

Open the Web URL and ensure it points to your API URL. If not, rebuild the Web image with the correct `VITE_API_BASE`.
