from flask import Blueprint, jsonify, current_app
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import text
from app.extensions import db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def get_health():
    """
    Returns application health status, database connectivity, and ML artifact availability.
    """
    db_status = "DISCONNECTED"
    db_error = None
    try:
        db.session.execute(text("SELECT 1"))
        db_status = "CONNECTED"
    except Exception as e:
        db_status = "ERROR"
        db_error = "Database connection check failed"

    model_path = Path(current_app.config['MODEL_PATH'])
    prep_path = Path(current_app.config['PREPROCESSOR_PATH'])

    model_available = model_path.exists()
    preprocessor_available = prep_path.exists()

    overall_status = "HEALTHY" if (db_status == "CONNECTED" and model_available and preprocessor_available) else "DEGRADED"

    return jsonify({
        'status': overall_status,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'environment': current_app.config['FLASK_ENV'],
        'dependencies': {
            'database': {
                'status': db_status,
                'type': 'PostgreSQL / Neon' if 'neon' in str(current_app.config['SQLALCHEMY_DATABASE_URI']) else 'SQLAlchemy Engine',
                'error': db_error
            },
            'ml_model': {
                'available': model_available,
                'path': str(model_path.name) if model_available else None
            },
            'preprocessor': {
                'available': preprocessor_available,
                'path': str(prep_path.name) if preprocessor_available else None
            }
        },
        'version': '1.0.0-aiml-final-year'
    }), 200
