import os
from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.alert import AlertNotification
from app.models.zone import Zone
from app.services.notification_service import NotificationService, AUTHORITY_REGISTRY

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """
    Returns list of emergency alert signals transmitted to authorities.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    zone_id = request.args.get('zone_id', type=int)
    authority_code = request.args.get('authority_code')

    query = AlertNotification.query
    if zone_id:
        query = query.filter_by(zone_id=zone_id)
    if authority_code:
        query = query.filter_by(authority_code=authority_code.upper())

    pagination = query.order_by(AlertNotification.dispatched_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'alerts': [a.to_dict() for a in pagination.items],
        'pagination': {
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }
    }), 200

@alerts_bp.route('/alerts/authorities', methods=['GET'])
def get_authorities():
    """
    Returns directory of registered disaster management authorities and contact relays.
    """
    return jsonify({
        'authorities': NotificationService.get_registered_authorities()
    }), 200

@alerts_bp.route('/alerts/summary', methods=['GET'])
def get_alerts_summary():
    """
    Returns aggregated alert dispatch metrics for the dashboard.
    """
    total_alerts = AlertNotification.query.count()
    critical_alerts = AlertNotification.query.filter_by(severity='CRITICAL_HIGH').count()
    latest_alert = AlertNotification.query.order_by(AlertNotification.dispatched_at.desc()).first()

    return jsonify({
        'total_dispatched': total_alerts,
        'critical_high_count': critical_alerts,
        'latest_dispatch': latest_alert.to_dict() if latest_alert else None,
        'registered_agencies_count': len(AUTHORITY_REGISTRY)
    }), 200

@alerts_bp.route('/alerts/broadcast', methods=['POST'])
def manual_broadcast():
    """
    Manual emergency drill / broadcast trigger for a specific zone.
    """
    data = request.get_json() or {}
    zone_id = data.get('zone_id')
    if not zone_id:
        return jsonify({'error': 'zone_id is required'}), 400

    authority_code = data.get('authority_code')

    try:
        dispatched = NotificationService.manual_broadcast_drill(
            zone_id=int(zone_id),
            authority_code=authority_code
        )
        return jsonify({
            'message': f'Emergency signal broadcast transmitted to {len(dispatched)} authority channels.',
            'count': len(dispatched),
            'alerts': [a.to_dict() for a in dispatched]
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Broadcast transmission error: {str(e)}'}), 500

@alerts_bp.route('/alerts/send-email', methods=['POST'])
def send_email_alert():
    """
    Sends an automated Disaster Alert Email containing Human Behavior Awareness
    guidelines to any specified authority or citizen email address.
    """
    from app.services.email_service import EmailService
    from app.models.prediction import Prediction
    data = request.get_json() or {}
    zone_id = data.get('zone_id')
    recipient_email = data.get('recipient_email', 'disaster-alerts@state.gov.in')

    if not zone_id:
        return jsonify({'error': 'zone_id is required'}), 400

    zone = db.session.get(Zone, int(zone_id))
    if not zone:
        return jsonify({'error': f'Zone {zone_id} not found'}), 404

    latest_pred = Prediction.query.filter_by(zone_id=zone.id)\
        .order_by(Prediction.assessment_timestamp.desc()).first()

    if not latest_pred:
        # Create a default high-risk prediction for demonstration if none exists
        from datetime import datetime, timezone
        latest_pred = Prediction(
            zone_id=zone.id,
            assessment_timestamp=datetime.now(timezone.utc),
            prediction_horizon_hours=24,
            prediction_target="Severe Storm & Flood Hazard",
            risk_score=0.825,
            risk_category="HIGH",
            input_features_snapshot={'rainfall_mm': 65.0, 'wind_speed_kmh': 70.0, 'pressure_hpa': 982.0}
        )
        db.session.add(latest_pred)
        db.session.commit()

    try:
        alert = EmailService.send_alert_email(
            to_email=recipient_email,
            zone=zone,
            prediction=latest_pred,
            authority_name="Disaster Management Authority & Citizens Email Dispatch"
        )
        is_live = "DELIVERED_VIA_SMTP" in alert.dispatch_status
        return jsonify({
            'message': f'Disaster Warning Email processed for {recipient_email}. Status: {alert.dispatch_status}',
            'alert': alert.to_dict(),
            'delivery_status': 'DELIVERED_VIA_SMTP' if is_live else alert.dispatch_status
        }), 201
    except Exception as e:
        return jsonify({'error': f'Failed to send email alert: {str(e)}'}), 500

@alerts_bp.route('/alerts/email-preview', methods=['GET'])
def get_email_preview():
    """
    Returns the Human Behavior Awareness guidelines and HTML email preview for a zone.
    """
    from app.services.email_service import EmailService
    from app.models.prediction import Prediction
    zone_id = request.args.get('zone_id', 1, type=int)
    zone = db.session.get(Zone, zone_id)
    if not zone:
        return jsonify({'error': f'Zone {zone_id} not found'}), 404

    latest_pred = Prediction.query.filter_by(zone_id=zone.id)\
        .order_by(Prediction.assessment_timestamp.desc()).first()

    if not latest_pred:
        from datetime import datetime, timezone
        latest_pred = Prediction(
            zone_id=zone.id,
            assessment_timestamp=datetime.now(timezone.utc),
            prediction_horizon_hours=24,
            prediction_target="Severe Storm & Flood Hazard",
            risk_score=0.825,
            risk_category="HIGH",
            input_features_snapshot={'rainfall_mm': 65.0, 'wind_speed_kmh': 70.0, 'pressure_hpa': 982.0}
        )

    guide = EmailService.generate_human_awareness_guide(zone, latest_pred.risk_score)
    subject, plain_text, html_content = EmailService.format_email_content(zone, latest_pred)

    return jsonify({
        'zone_id': zone.id,
        'zone_code': zone.zone_code,
        'zone_name': zone.name,
        'risk_score': latest_pred.risk_score,
        'risk_category': latest_pred.risk_category,
        'email_subject': subject,
        'email_plain_text': plain_text,
        'email_html': html_content,
        'human_awareness_guide': guide
    }), 200

@alerts_bp.route('/alerts/smtp-config', methods=['GET', 'POST'])
def manage_smtp_config():
    """
    Retrieves or updates live SMTP email gateway configuration.
    """
    from app.services.email_service import EmailService
    if request.method == 'GET':
        return jsonify(EmailService.get_smtp_config()), 200

    data = request.get_json() or {}
    server = data.get('server', '').strip()
    port = int(data.get('port', 587))
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    sender = data.get('sender', '').strip() or username

    if not server:
        return jsonify({'error': 'SMTP server is required'}), 400

    config = EmailService.save_smtp_config(
        server=server,
        port=port,
        username=username,
        password=password,
        sender=sender
    )
    return jsonify({
        'message': 'SMTP configuration updated and persisted successfully.',
        'config': config
    }), 200

@alerts_bp.route('/alerts/test-smtp', methods=['POST'])
def test_smtp():
    """
    Tests live SMTP connection with provided or saved credentials.
    """
    from app.services.email_service import EmailService
    data = request.get_json() or {}
    server = data.get('server') or os.getenv('MAIL_SERVER')
    port = int(data.get('port') or os.getenv('MAIL_PORT', 587))
    username = data.get('username') or os.getenv('MAIL_USERNAME')
    password = data.get('password') or os.getenv('MAIL_PASSWORD')
    sender = data.get('sender') or os.getenv('MAIL_DEFAULT_SENDER') or username
    recipient = data.get('recipient_test') or username

    if not server or not username or not password:
        return jsonify({
            'error': 'Missing SMTP configuration. Please provide server, username, and password.'
        }), 400

    try:
        res = EmailService.test_smtp_connection(
            server=server,
            port=port,
            username=username,
            password=password,
            sender=sender,
            recipient_test=recipient
        )
        return jsonify(res), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 422
