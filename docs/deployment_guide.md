# Production Deployment & Neon PostgreSQL Integration Guide

This guide details the procedures for configuring, securing, and deploying the **AI Micro-Zone Disaster Prediction System** across cloud hosting environments and Windows servers.

---

## 1. Neon PostgreSQL Database Setup

### 1.1 Creating a Neon PostgreSQL Database
1. Sign up or log into [Neon Console](https://console.neon.tech).
2. Create a new project: e.g., `disaster-prediction-prod`.
3. Select your preferred AWS region (e.g., `us-east-2`, `ap-south-1`).
4. In the Project Dashboard, navigate to the **Connection Details** section.
5. Select **Pooled Connection** (recommended for serverless workloads) or **Direct Connection**.
6. Ensure the connection string format matches:
   ```env
   postgresql://neondb_owner:YOUR_PASSWORD@ep-xyz-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

### 1.2 Neon Connection & SSL Configuration
Neon PostgreSQL **mandates TLS/SSL encrypted connections**. The backend automatically detects Neon hosts and enforces `sslmode=require` if absent from the connection query parameter.

In `backend/app/config.py`:
```python
raw_db_url = os.getenv('DATABASE_URL')
if raw_db_url.startswith('postgres://'):
    raw_db_url = raw_db_url.replace('postgres://', 'postgresql://', 1)

if 'neon.tech' in raw_db_url and 'sslmode=' not in raw_db_url:
    separator = '&' if '?' in raw_db_url else '?'
    raw_db_url = f"{raw_db_url}{separator}sslmode=require"

SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
```

---

## 2. Environment Variables Configuration

Create a production `.env` file in the `backend/` directory (never commit `.env` to source control):

```env
# Flask Core
FLASK_ENV=production
SECRET_KEY=generate-a-strong-64-char-random-hex-string
PORT=5000
HOST=0.0.0.0

# Neon PostgreSQL
DATABASE_URL=postgresql://user:password@ep-sample-1234.us-east-2.aws.neon.tech/neondb?sslmode=require

# Restricted CORS (Comma-separated production domains)
CORS_ALLOWED_ORIGINS=https://your-production-app.vercel.app,https://your-domain.com

# Artifact Paths
MODEL_PATH=artifacts/models/lstm_disaster_model.keras
PREPROCESSOR_PATH=artifacts/preprocessing/preprocessor.joblib
```

For the frontend (`frontend/.env`):
```env
VITE_API_BASE_URL=https://your-api-domain.com/api/v1
```
*(Notice: Never expose database credentials or secret keys in the frontend build.)*

---

## 3. Database Initialization & Migrations

Initialize database schemas and apply migrations cleanly without deleting existing historical data:

```powershell
# Set environment
$env:FLASK_APP = "run.py"
$env:DATABASE_URL = "postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Initialize Alembic migrations repository
.\venv\Scripts\flask db init

# Generate initial migration script
.\venv\Scripts\flask db migrate -m "Initial micro-zone schema with Neon PostgreSQL"

# Apply migrations to Neon database
.\venv\Scripts\flask db upgrade
```

---

## 4. Serving the Backend with Production WSGI

Flask's built-in development server (`flask run`) is intended only for local development.

### 4.1 On Windows Production Environments (Waitress)
Waitress is installed in the project dependencies and is natively compatible with Windows:

```powershell
# In PowerShell:
$env:FLASK_ENV = "production"
.\venv\Scripts\python.exe run.py
```
This automatically invokes `waitress.serve(app, host='0.0.0.0', port=5000, threads=8)`.

### 4.2 On Linux Production Environments (Gunicorn)
In Linux containers, cloud VMs, or PaaS providers (e.g., Render, Railway, AWS EC2):

```bash
gunicorn -w 4 -k sync --timeout 120 -b 0.0.0.0:5000 run:app
```

---

## 5. Frontend Production Build & Deployment

Compile the static bundle with Vite:

```powershell
cd frontend
npm run build
```

The resulting optimized bundle is located in `frontend/dist/` and can be deployed directly to:
- **Vercel**: Import repository root, set root directory to `frontend`.
- **Netlify**: Set build command to `npm run build` and publish directory to `dist`.
- **Nginx**: Host `frontend/dist/` as static assets with reverse proxy to `/api/v1` on port 5000.

---

## 6. Health & Liveness Checks

Automated monitoring tools (e.g., Uptime Kuma, AWS Route 53, Datadog) should query:
```http
GET https://your-api-domain.com/api/v1/health
```

Expected Response:
```json
{
  "status": "HEALTHY",
  "dependencies": {
    "database": {
      "status": "CONNECTED",
      "type": "PostgreSQL / Neon"
    },
    "ml_model": {
      "available": true,
      "path": "lstm_disaster_model.keras"
    },
    "preprocessor": {
      "available": true,
      "path": "preprocessor.joblib"
    }
  },
  "version": "1.0.0-aiml-final-year"
}
```
