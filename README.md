# Human Behavior Aware Micro-Zone Disaster Prediction System Using AI

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-emerald.svg)](https://palletsprojects.com/p/flask/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.21-orange.svg)](https://www.tensorflow.org/)
[![React](https://img.shields.io/badge/React-19-cyan.svg)](https://react.dev/)
[![Neon PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon%20Serverless-indigo.svg)](https://neon.tech/)
[![Tests](https://img.shields.io/badge/pytest-21%20Passed%20(100%25)-brightgreen.svg)]()

> **Final-Year Project**: HUMAN BEHAVIOR AWARE MICRO-ZONE DISASTER PREDICTION SYSTEM USING AI
> A decision-support system that predicts localized disasters from 5 years of historical disaster data, guides humans on how to be aware and stay safe, and automatically sends disaster alert notifications via email.

---

## 🌟 The 4 Core Pillars of the Project

1. **5-Year Historical Disaster Data**:
   - The system uses 5 years of continuous historical hydro-meteorological data (rainfall, temperature, humidity, wind, pressure, soil moisture).
   - The AI model studies this 5-year history to recognize which weather conditions lead to flash floods and severe storms.

2. **Micro-Zone Disaster Prediction**:
   - Instead of predicting for an entire state, the region is divided into localized **Micro-Zones** (Coastal Lowland, River Basin, Urban Metro).
   - Classifies risk into **Low Risk (< 35%)**, **Medium Risk (35%–70%)**, and **High Risk (≥ 70%)**.

3. **Human Behavior Awareness ("How Humans Become Aware")**:
   - Provides clear, actionable safety instructions for the public:
     - 🏃 **Immediate Actions**: Evacuate to higher municipal shelters, turn off electrical mains and gas.
     - 🎒 **Emergency Kit Checklist**: 3-day drinking water, food rations, torch, medicines, waterproof documents.
     - 🤝 **Community Behavior**: Do not spread unverified rumors, assist elderly and vulnerable neighbors.
     - 📞 **Emergency Contacts**: DDMA (1077), State SEOC (1070), NDRF (044-27473000), Municipal (1913).

4. **Automated Email Alert Notifications**:
   - Whenever High Risk is detected, the system **automatically sends a Disaster Warning Email** to registered authorities and citizens containing the hazard alert and the complete Human Safety Advisory.

---

## 2. Project Directory Structure

```
micropred/
├── frontend/
│   ├── src/
│   │   ├── components/       # RiskBadge, MicroZoneMap, WeatherTrendChart, RiskPieChart, etc.
│   │   ├── pages/            # Dashboard, MicroZones, PredictionHistory, Reports, DatasetStatus
│   │   ├── layouts/          # Responsive Layout with live system health and modal disclaimers
│   │   ├── services/
│   │   │   └── api.js        # Centralized Axios client with /api/v1 base URL
│   │   ├── App.jsx           # React Router DOM configuration
│   │   ├── main.jsx
│   │   └── index.css         # Leaflet styles and Tailwind base directives
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── .env.example
│   └── .env
├── backend/
│   ├── app/
│   │   ├── __init__.py       # Application factory with CORS & Blueprints
│   │   ├── config.py         # Neon PostgreSQL SSL and environment configuration
│   │   ├── extensions.py     # SQLAlchemy, Migrate, CORS
│   │   ├── models/           # Zone, WeatherObservation, DisasterEvent, Prediction, etc.
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── routes/           # health, dashboard, zones, predictions, datasets, reports
│   │   ├── services/         # Risk engine, prediction service, data seeding & exports
│   │   ├── ml/               # LSTM model, preprocessor, dataset loader, evaluate, train
│   │   └── utils/            # Structured logging
│   ├── tests/                # 21 automated pytest test suites
│   ├── requirements.txt      # Pinned backend dependencies
│   ├── run.py                # WSGI entrypoint with Waitress/Flask support
│   ├── .env.example
│   └── .env
├── data/
│   ├── raw/                  # historical_disaster_weather.csv
│   └── processed/
├── artifacts/
│   ├── models/               # lstm_disaster_model.keras
│   └── preprocessing/        # preprocessor.joblib
├── scripts/
│   ├── train_model.py        # Model training and DB registration script
│   └── run_system.ps1        # PowerShell convenience orchestrator
├── docs/
│   ├── architecture.md
│   ├── scientific_limitations.md
│   └── deployment_guide.md
├── .gitignore
└── README.md
```

---

## 3. Windows PowerShell Installation & Setup Guide

Execute the following commands sequentially in Windows PowerShell.

### Step 1: Verify Python and Node.js Versions
```powershell
python --version   # Requires Python 3.11+ (Verified on Python 3.13)
node -v            # Requires Node.js 18+ (Verified on Node v24)
npm -v
```

### Step 2: Create and Activate Python Virtual Environment
```powershell
cd D:\micropred
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Backend Dependencies
```powershell
.\venv\Scripts\pip.exe install -r backend\requirements.txt
```

### Step 4: Install Frontend Dependencies
```powershell
cd D:\micropred\frontend
npm install
cd D:\micropred
```

### Step 5: Configure Environment Files
Backend environment (`backend/.env`):
```env
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production-disaster-sys
PORT=5000
DATABASE_URL=sqlite:///D:/micropred/disaster_dev.db
# For Neon PostgreSQL, replace with your Neon connection URL:
# DATABASE_URL=postgresql://user:password@ep-sample-1234.us-east-2.aws.neon.tech/neondb?sslmode=require
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MODEL_PATH=D:/micropred/artifacts/models/lstm_disaster_model.keras
PREPROCESSOR_PATH=D:/micropred/artifacts/preprocessing/preprocessor.joblib
```

Frontend environment (`frontend/.env`):
```env
VITE_API_BASE_URL=http://localhost:5000/api/v1
```

### Step 6: Connect Neon PostgreSQL (Optional Cloud Database)
To use Neon PostgreSQL instead of the local SQLite development database:
1. Obtain your connection string from the [Neon Console](https://console.neon.tech).
2. Ensure `sslmode=require` is present at the end of the query parameters.
3. Update `DATABASE_URL` in `backend/.env`.

### Step 7: Train the Stacked LSTM Model & Generate Artifacts
Executes dataset schema validation, chronological train/val/test splitting, scaler fitting, and trains the stacked LSTM model:
```powershell
.\venv\Scripts\python.exe scripts\train_model.py
```
*Outputs: `artifacts/models/lstm_disaster_model.keras` and `artifacts/preprocessing/preprocessor.joblib`.*

### Step 8: Initialize and Seed the Database
Populates initial micro-zones and 2,500 historical weather observations:
```powershell
.\venv\Scripts\python.exe -c "from run import init_db; init_db()"
```

### Step 9: Run Automated Tests
Execute the comprehensive test suite (21 unit and integration tests):
```powershell
cd D:\micropred\backend
..\venv\Scripts\pytest.exe -v
cd D:\micropred
```
*Result: 21 passed (100% success rate).*

### Step 10: Start Backend & Frontend Servers

**Terminal 1 (Flask Backend):**
```powershell
cd D:\micropred\backend
..\venv\Scripts\python.exe run.py
```
*Backend runs on `http://127.0.0.1:5000` (Health check: `http://127.0.0.1:5000/api/v1/health`).*

**Terminal 2 (React Frontend):**
```powershell
cd D:\micropred\frontend
npm run dev
```
*Frontend runs on `http://localhost:5173`.*

> **Diagnosing Port Conflicts:** If port 5000 is occupied by another application, run:  
> `netstat -ano | findstr :5000`  
> To run on a different port, set `$env:PORT="5001"` in Terminal 1 and update `VITE_API_BASE_URL=http://localhost:5001/api/v1` in `frontend/.env`.

---

## 4. Empirical Evaluation Results

The stacked LSTM model was trained on 180 days of hourly observations across 5 micro-zones (8,640 records). Evaluation was performed on an untouched chronological test set (15% chronological split with no future lookahead leakage):

| Metric | Stacked LSTM Model | Baseline (Logistic Regression) |
| :--- | :--- | :--- |
| **ROC-AUC Score** | **0.7375** | 0.7254 |
| **Accuracy** | **82.93%** | 82.49% |
| **Brier Score** | **0.1279** | 0.1412 |
| **Lookback Sequence** | 24 Hours | Flattened 24 Hours |
| **Forecast Horizon** | 24 Hours | 24 Hours |

---

## 5. Scientific Limitations Disclosure

1. **Academic Decision-Support Nature**: This application is built as an academic capstone project. Outputs are decision-support probabilities, not official government evacuation orders.
2. **Behavioral Data Prospective Status**: In accordance with research integrity standards, the initial operational pipeline focuses exclusively on verified historical hydro-meteorological features. Human crowd sensor dynamics (CCTV tracking, cellular movement, social sentiment) are treated as future work pending privacy-compliant field datasets.
3. **Geospatial Demarcations**: Zone boundaries are modeled using circular centroid buffers rather than official legal cadastral boundaries.

For detailed discussion, see [`docs/scientific_limitations.md`](docs/scientific_limitations.md).
