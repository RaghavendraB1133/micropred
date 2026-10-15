from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from app.extensions import db
from app.models.prediction import Prediction
from app.models.zone import Zone
from app.schemas.validation import PredictionRunRequest
from app.services.prediction_service import PredictionService

predictions_bp = Blueprint('predictions', __name__)

@predictions_bp.route('/predictions', methods=['GET'])
def get_predictions():
    """
    Returns paginated prediction history with optional filters.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    zone_id = request.args.get('zone_id', type=int)
    risk_category = request.args.get('risk_category')

    query = Prediction.query
    if zone_id:
        query = query.filter_by(zone_id=zone_id)
    if risk_category:
        query = query.filter_by(risk_category=risk_category.upper())

    pagination = query.order_by(Prediction.assessment_timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'predictions': [p.to_dict() for p in pagination.items],
        'pagination': {
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }
    }), 200

@predictions_bp.route('/predictions/<int:prediction_id>', methods=['GET'])
def get_prediction_by_id(prediction_id: int):
    pred = db.session.get(Prediction, prediction_id)
    if not pred:
        return jsonify({'error': f'Prediction {prediction_id} not found'}), 404
    return jsonify(pred.to_dict()), 200

@predictions_bp.route('/predictions/run', methods=['POST'])
def run_prediction():
    """
    Executes an inference run for a specific micro-zone using the trained LSTM model.
    """
    data = request.get_json() or {}
    try:
        validated = PredictionRunRequest(**data)
    except ValidationError as e:
        return jsonify({'error': 'Invalid request parameters', 'details': e.errors()}), 422

    try:
        prediction = PredictionService.run_prediction_for_zone(
            zone_id=validated.zone_id,
            horizon_hours=validated.horizon_hours
        )
        return jsonify({
            'message': 'Prediction successfully generated and recorded.',
            'prediction': prediction.to_dict()
        }), 201
    except FileNotFoundError as e:
        return jsonify({'error': str(e), 'code': 'MODEL_NOT_AVAILABLE'}), 503
    except ValueError as e:
        return jsonify({'error': str(e), 'code': 'INSUFFICIENT_DATA'}), 400
    except Exception as e:
        return jsonify({'error': f'Inference engine error: {str(e)}'}), 500

@predictions_bp.route('/predictions/batch', methods=['POST'])
def run_batch_predictions():
    """
    Executes predictions for all active micro-zones.
    """
    try:
        predictions = PredictionService.run_batch_predictions()
        return jsonify({
            'message': f'Batch prediction completed for {len(predictions)} zones.',
            'count': len(predictions),
            'predictions': [p.to_dict() for p in predictions]
        }), 200
    except FileNotFoundError as e:
        return jsonify({'error': str(e), 'code': 'MODEL_NOT_AVAILABLE'}), 503
    except Exception as e:
        return jsonify({'error': f'Batch inference error: {str(e)}'}), 500

@predictions_bp.route('/predictions/simulate-scenario', methods=['POST'])
def simulate_scenario():
    """
    Injects a disaster meteorological scenario (e.g. storm_surge, flash_flood, calm)
    and executes multi-zone prediction inference.
    """
    data = request.get_json() or {}
    scenario_name = data.get('scenario', 'storm_surge').lower()

    try:
        predictions = PredictionService.simulate_scenario(scenario_name)
        return jsonify({
            'message': f'Successfully simulated {scenario_name} hazard scenario across micro-zones.',
            'scenario': scenario_name,
            'count': len(predictions),
            'predictions': [p.to_dict() for p in predictions]
        }), 200
    except FileNotFoundError as e:
        return jsonify({'error': str(e), 'code': 'MODEL_NOT_AVAILABLE'}), 503
    except Exception as e:
        return jsonify({'error': f'Scenario simulation error: {str(e)}'}), 500

@predictions_bp.route('/predictions/future-forecast', methods=['GET', 'POST'])
def get_future_disaster_forecast():
    """
    Generates multi-horizon future disaster forecasts for a micro-zone based on
    previous historical observation data.
    """
    zone_id = None
    horizons = None
    if request.method == 'POST':
        data = request.get_json() or {}
        zone_id = data.get('zone_id')
        horizons = data.get('horizons')
    else:
        zone_id = request.args.get('zone_id', type=int)
        horizons_raw = request.args.get('horizons')
        if horizons_raw:
            try:
                horizons = [int(h.strip()) for h in horizons_raw.split(',') if h.strip()]
            except ValueError:
                horizons = None

    # If zone_id not specified, find zone with highest risk prediction or first active zone
    if not zone_id:
        top_risk_pred = Prediction.query.order_by(Prediction.risk_score.desc()).first()
        if top_risk_pred:
            zone_id = top_risk_pred.zone_id
        else:
            first_zone = Zone.query.filter_by(is_active=True).first()
            if first_zone:
                zone_id = first_zone.id

    if not zone_id:
        return jsonify({'error': 'No active micro-zone found in database'}), 404

    try:
        forecast_result = PredictionService.forecast_future_disaster(
            zone_id=zone_id,
            horizons=horizons
        )
        return jsonify(forecast_result), 200
    except ValueError as e:
        return jsonify({'error': str(e), 'code': 'INSUFFICIENT_DATA'}), 400
    except FileNotFoundError as e:
        return jsonify({'error': str(e), 'code': 'MODEL_NOT_AVAILABLE'}), 503
    except Exception as e:
        return jsonify({'error': f'Future forecast inference error: {str(e)}'}), 500

