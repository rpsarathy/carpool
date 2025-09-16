# Google OAuth Setup Guide

This guide will help you set up Google OAuth authentication for the Carpool app.

## Prerequisites

- Google Cloud Console account
- Access to your carpool app project

## Step 1: Create Google OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project or create a new one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
5. If prompted, configure the OAuth consent screen first:
   - Choose **External** user type
   - Fill in the required fields:
     - App name: "Carpool App"
     - User support email: your email
     - Developer contact information: your email
   - Add scopes: `email`, `profile`, `openid`
   - Add test users if needed

6. Create OAuth client ID:
   - Application type: **Web application**
   - Name: "Carpool Web Client"
   - Authorized JavaScript origins:
     - `http://localhost:5173` (for local development)
     - `https://your-production-domain.com` (for production)
   - Authorized redirect URIs:
     - `http://localhost:5173` (for local development)
     - `https://your-production-domain.com` (for production)

7. Copy the **Client ID** and **Client Secret**

## Step 2: Configure Backend Environment

1. Copy `env.example` to `.env`:
   ```bash
   cp env.example .env
   ```

2. Update `.env` with your Google OAuth credentials:
   ```bash
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```

## Step 3: Configure Frontend Environment

1. In the `web/` directory, copy `env.example` to `.env`:
   ```bash
   cd web
   cp env.example .env
   ```

2. Update `web/.env` with your Google Client ID:
   ```bash
   VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   VITE_API_BASE=http://localhost:8000
   ```

## Step 4: Install Dependencies and Run Migration

1. Install backend dependencies:
   ```bash
   pip install -e .
   ```

2. Install frontend dependencies:
   ```bash
   cd web
   npm install
   ```

3. Run database migration:
   ```bash
   cd ..
   alembic upgrade head
   ```

## Step 5: Test the Integration

1. Start the backend server:
   ```bash
   python start_server.py
   ```

2. In a new terminal, start the frontend:
   ```bash
   cd web
   npm run dev
   ```

3. Navigate to `http://localhost:5173`
4. Try signing up or logging in with Google

## Production Deployment

### Backend (Cloud Run)

Update your Cloud Run service environment variables:
```bash
gcloud run services update carpool-api \
  --set-env-vars GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com \
  --set-env-vars GOOGLE_CLIENT_SECRET=your-google-client-secret \
  --region us-central1
```

### Frontend (Cloud Run)

Update your web build arguments in `cloudbuild.web.yaml`:
```yaml
args:
  - '--build-arg'
  - 'VITE_API_BASE=https://carpool-api-dzxkfcfuiq-uc.a.run.app'
  - '--build-arg'
  - 'VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com'
```

## Security Notes

- Never commit your `.env` files to version control
- Use different Google OAuth clients for development and production
- Regularly rotate your client secrets
- Monitor OAuth usage in Google Cloud Console

## Troubleshooting

### Common Issues

1. **"Google Auth not initialized" error**
   - Check that `VITE_GOOGLE_CLIENT_ID` is set correctly
   - Verify the Google script is loading properly

2. **"Invalid Google token" error**
   - Ensure your domain is added to authorized origins
   - Check that the client ID matches between frontend and backend

3. **CORS errors**
   - Verify your domain is in the authorized origins list
   - Check that the API CORS configuration includes your frontend domain

4. **Database errors**
   - Run the migration: `alembic upgrade head`
   - Check that the `google_id` column exists in the users table

### Testing OAuth Flow

You can test the OAuth endpoints directly:

```bash
# Test Google OAuth endpoint
curl -X POST http://localhost:8000/auth/google \
  -H "Content-Type: application/json" \
  -d '{"id_token": "your-google-id-token"}'
```

## Support

If you encounter issues, check:
1. Google Cloud Console logs
2. Browser developer console
3. Backend server logs
4. Network tab for failed requests
