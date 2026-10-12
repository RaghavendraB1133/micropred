import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend root or workspace root
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret-key-disaster-sys-2026')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = False
    TESTING = False

    # Database URL Handling with Neon PostgreSQL support
    raw_db_url = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR / "disaster_dev.db"}')
    if raw_db_url.startswith('postgres://'):
        raw_db_url = raw_db_url.replace('postgres://', 'postgresql://', 1)
    
    # Ensure Neon SSL mode is present if neon.tech is in host
    if 'neon.tech' in raw_db_url and 'sslmode=' not in raw_db_url:
        separator = '&' if '?' in raw_db_url else '?'
        raw_db_url = f"{raw_db_url}{separator}sslmode=require"

    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # CORS configuration
    CORS_ALLOWED_ORIGINS = [
        origin.strip() for origin in os.getenv(
            'CORS_ALLOWED_ORIGINS',
            'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000'
        ).split(',') if origin.strip()
    ]

    # Paths
    ARTIFACTS_DIR = BASE_DIR / 'artifacts'
    MODELS_DIR = ARTIFACTS_DIR / 'models'
    PREPROCESSING_DIR = ARTIFACTS_DIR / 'preprocessing'
    DATA_DIR = BASE_DIR / 'data'
    RAW_DATA_DIR = DATA_DIR / 'raw'
    PROCESSED_DATA_DIR = DATA_DIR / 'processed'

    MODEL_PATH = Path(os.getenv('MODEL_PATH', str(MODELS_DIR / 'lstm_disaster_model.keras')))
    PREPROCESSOR_PATH = Path(os.getenv('PREPROCESSOR_PATH', str(PREPROCESSING_DIR / 'preprocessor.joblib')))

    # ML Parameters
    LOOKBACK_STEPS = 24  # 24 historical hours
    FORECAST_HORIZON_HOURS = 24  # 24h forward hazard window
    FEATURES = [
        'rainfall_mm',
        'temperature_c',
        'humidity_pct',
        'wind_speed_kmh',
        'pressure_hpa',
        'soil_moisture_pct'
    ]

    # Risk Engine Thresholds (Configurable)
    # Binary disaster score: [0.0, 1.0]
    RISK_THRESHOLD_LOW = 0.35      # Score < 0.35 -> LOW
    RISK_THRESHOLD_HIGH = 0.70     # Score >= 0.70 -> HIGH, else MEDIUM

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max dataset file upload

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    CORS_ALLOWED_ORIGINS = ['*']

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
