from flask import Blueprint, jsonify, current_app
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import func
from app.extensions import db
from app.models.zone import Zone
from app.models.prediction import Prediction
from app.models.weather import WeatherObservation
from app.models.dataset import DatasetMetadata
from app.models.model_version import ModelVersion
from app.models.alert import AlertNotification

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """
    Returns aggregated metrics, risk distribution, latest predictions,
    and system status for the main dashboard.
    """
    total_zones = Zone.query.filter_by(is_active=True).count()
    total_predictions = Prediction.query.count()

    # Get the latest prediction for each zone to calculate current active risk distribution
    subquery = db.session.query(
        Prediction.zone_id,
        func.max(Prediction.assessment_timestamp).label('max_time')
    ).group_by(Prediction.zone_id).subquery()

    latest_per_zone = db.session.query(Prediction).join(
        subquery,
        (Prediction.zone_id == subquery.c.zone_id) &
        (Prediction.assessment_timestamp == subquery.c.max_time)
    ).all()

    risk_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
    for p in latest_per_zone:
        cat = p.risk_category.upper()
        if cat in risk_counts:
            risk_counts[cat] += 1

    # Latest overall prediction
    latest_pred = Prediction.query.order_by(Prediction.assessment_timestamp.desc()).first()
    latest_timestamp = latest_pred.assessment_timestamp.isoformat() if latest_pred else None

    # Dataset status
    dataset_count = DatasetMetadata.query.count()
    latest_dataset = DatasetMetadata.query.order_by(DatasetMetadata.created_at.desc()).first()

    # Model status
    model_path = Path(current_app.config['MODEL_PATH'])
    prep_path = Path(current_app.config['PREPROCESSOR_PATH'])
    model_available = model_path.exists() and prep_path.exists()
    active_model = ModelVersion.query.filter_by(is_active=True).first()

    # Recent weather trend (last 24 observations across zones for charting)
    recent_weather = WeatherObservation.query.order_by(WeatherObservation.timestamp.desc()).limit(24).all()
    weather_trend = [
        {
            'timestamp': obs.timestamp.strftime('%H:%M %d-%b'),
            'rainfall_mm': obs.rainfall_mm,
            'temperature_c': obs.temperature_c,
            'humidity_pct': obs.humidity_pct,
            'wind_speed_kmh': obs.wind_speed_kmh,
            'pressure_hpa': obs.pressure_hpa,
            'soil_moisture_pct': obs.soil_moisture_pct,
        }
        for obs in reversed(recent_weather)
    ]

    # Recent predictions (last 10)
    recent_preds = Prediction.query.order_by(Prediction.assessment_timestamp.desc()).limit(10).all()

    # Recent authority alert signals (last 10)
    recent_alerts = AlertNotification.query.order_by(AlertNotification.dispatched_at.desc()).limit(10).all()

    return jsonify({
        'summary': {
            'total_zones': total_zones,
            'total_predictions': total_predictions,
            'latest_prediction_timestamp': latest_timestamp,
            'risk_counts': risk_counts,
            'low_risk_count': risk_counts['LOW'],
            'medium_risk_count': risk_counts['MEDIUM'],
            'high_risk_count': risk_counts['HIGH'],
            'alerts_dispatched_count': AlertNotification.query.count(),
        },
        'latest_predictions': [p.to_dict() for p in recent_preds],
        'authority_alerts': [a.to_dict() for a in recent_alerts],
        'weather_trends': weather_trend,
        'system_status': {
            'model_available': model_available,
            'model_version': active_model.version_tag if active_model else ('v1.0-lstm-hazard' if model_available else 'NOT_TRAINED'),
            'dataset_count': dataset_count,
            'dataset_status': latest_dataset.validation_status if latest_dataset else 'NO_DATASET',
        },
        'scientific_disclaimer': {
            'is_academic_system': True,
            'human_behavior_status': 'Limitation: Behavioral metrics excluded pending empirical field data.',
            'hazard_type': 'Hydrometeorological Severe Weather & Flash Flood Hazard'
        }
    }), 200
