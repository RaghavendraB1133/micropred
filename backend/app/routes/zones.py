from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.zone import Zone
from app.models.weather import WeatherObservation
from app.models.prediction import Prediction
from app.models.disaster import DisasterEvent

zones_bp = Blueprint('zones', __name__)

@zones_bp.route('/zones', methods=['GET'])
def get_zones():
    """
    Returns list of micro-zones with their latest prediction risk level.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    is_active = request.args.get('is_active', None)

    query = Zone.query
    if is_active is not None:
        active_bool = is_active.lower() in ('true', '1')
        query = query.filter_by(is_active=active_bool)

    zones_pagination = query.order_by(Zone.id.asc()).paginate(page=page, per_page=per_page, error_out=False)

    zones_data = []
    for z in zones_pagination.items:
        z_dict = z.to_dict()
        latest_pred = Prediction.query.filter_by(zone_id=z.id)\
            .order_by(Prediction.assessment_timestamp.desc()).first()
        z_dict['latest_prediction'] = latest_pred.to_dict() if latest_pred else None
        zones_data.append(z_dict)

    return jsonify({
        'zones': zones_data,
        'pagination': {
            'total': zones_pagination.total,
            'page': zones_pagination.page,
            'per_page': zones_pagination.per_page,
            'pages': zones_pagination.pages
        }
    }), 200

@zones_bp.route('/zones/<int:zone_id>', methods=['GET'])
def get_zone_by_id(zone_id: int):
    zone = db.session.get(Zone, zone_id)
    if not zone:
        return jsonify({'error': f'Zone {zone_id} not found'}), 404

    z_dict = zone.to_dict()
    latest_pred = Prediction.query.filter_by(zone_id=zone.id)\
        .order_by(Prediction.assessment_timestamp.desc()).first()
    z_dict['latest_prediction'] = latest_pred.to_dict() if latest_pred else None
    return jsonify(z_dict), 200

@zones_bp.route('/zones/<int:zone_id>/history', methods=['GET'])
def get_zone_history(zone_id: int):
    zone = db.session.get(Zone, zone_id)
    if not zone:
        return jsonify({'error': f'Zone {zone_id} not found'}), 404

    limit = request.args.get('limit', 100, type=int)
    
    # Weather observations
    observations = WeatherObservation.query.filter_by(zone_id=zone_id)\
        .order_by(WeatherObservation.timestamp.desc()).limit(limit).all()

    # Past disaster records
    disasters = DisasterEvent.query.filter_by(zone_id=zone_id)\
        .order_by(DisasterEvent.timestamp.desc()).limit(20).all()

    # Past predictions
    predictions = Prediction.query.filter_by(zone_id=zone_id)\
        .order_by(Prediction.assessment_timestamp.desc()).limit(20).all()

    return jsonify({
        'zone': zone.to_dict(),
        'weather_history': [obs.to_dict() for obs in reversed(observations)],
        'disaster_events': [d.to_dict() for d in disasters],
        'prediction_history': [p.to_dict() for p in predictions]
    }), 200

@zones_bp.route('/zones/<int:zone_id>/sync-live', methods=['POST'])
def sync_zone_live_weather(zone_id: int):
    """
    Fetches real-time live internet meteorological data for this zone
    from Open-Meteo API and stores the latest 24 hours in the database.
    """
    from app.services.live_weather_service import LiveWeatherService
    try:
        result = LiveWeatherService.sync_zone_live_weather(zone_id)
        return jsonify({
            'message': f'Live internet weather successfully synchronized for Zone {result["zone_code"]}.',
            'sync_details': result
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Live weather synchronization failed: {str(e)}'}), 502

@zones_bp.route('/zones/sync-live-all', methods=['POST'])
def sync_all_zones_live_weather():
    """
    Synchronizes real-time live internet weather for all active micro-zones.
    """
    from app.services.live_weather_service import LiveWeatherService
    try:
        results = LiveWeatherService.sync_all_zones_live_weather()
        return jsonify({
            'message': f'Successfully synchronized live internet weather across {len(results)} zones.',
            'results': results
        }), 200
    except Exception as e:
        return jsonify({'error': f'Live weather batch sync failed: {str(e)}'}), 502

@zones_bp.route('/zones/seed-pan-india', methods=['POST'])
def seed_pan_india():
    """
    Populates comprehensive disaster-prone micro-zones across all regions of India
    (North, South, East, West, and Central India).
    """
    from app.services.pan_india_service import PanIndiaService
    try:
        zones = PanIndiaService.seed_all_india_zones_if_needed()
        return jsonify({
            'message': f'Pan-India disaster monitoring network successfully initialized with {len(zones)} active zones.',
            'count': len(zones),
            'zones': [z.to_dict() for z in zones]
        }), 201
    except Exception as e:
        return jsonify({'error': f'Failed to seed Pan-India zones: {str(e)}'}), 500

@zones_bp.route('/zones/add-custom', methods=['POST'])
def add_custom_location():
    """
    Adds ANY custom geographic location across India to the disaster monitoring network.
    """
    from app.services.pan_india_service import PanIndiaService
    data = request.get_json() or {}
    name = data.get('name')
    lat = data.get('latitude')
    lon = data.get('longitude')
    state = data.get('state')
    topography = data.get('topography')

    if not name or lat is None or lon is None:
        return jsonify({'error': 'name, latitude, and longitude are required'}), 400

    try:
        lat_f = float(lat)
        lon_f = float(lon)
        if not (6.0 <= lat_f <= 38.0 and 68.0 <= lon_f <= 98.0):
            return jsonify({
                'error': f'Coordinates ({lat_f}, {lon_f}) are outside the territory of India (Lat: 6°-38°N, Lon: 68°-98°E).'
            }), 400

        result = PanIndiaService.add_custom_location(
            name=name,
            latitude=lat_f,
            longitude=lon_f,
            state=state,
            topography=topography
        )
        return jsonify(result), 201
    except ValueError:
        return jsonify({'error': 'Invalid latitude or longitude numbers'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to add custom location: {str(e)}'}), 500
