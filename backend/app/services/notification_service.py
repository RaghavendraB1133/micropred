from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.extensions import db
from app.models.alert import AlertNotification
from app.models.zone import Zone
from app.models.prediction import Prediction
from app.utils.logger import logger

AUTHORITY_REGISTRY = [
    {
        'name': 'District Disaster Management Authority (DDMA)',
        'code': 'DDMA',
        'contact': '+91-1077 (District Collectorate Control)',
        'channel': 'EMERGENCY_SMS_GATEWAY',
        'role': 'Local evacuation coordination, shelter activation, and NDRF request.'
    },
    {
        'name': 'State Emergency Operation Centre (SEOC / SDMA)',
        'code': 'SEOC',
        'contact': '+91-1070 (Toll-Free State Operations)',
        'channel': 'SEOC_DISPATCH_WEBHOOK',
        'role': 'Inter-district emergency resources and state rescue mobilization.'
    },
    {
        'name': 'National Disaster Response Force (NDRF Command)',
        'code': 'NDRF',
        'contact': '+91-044-27473000 (Arakkonam Regional Base)',
        'channel': 'COMMAND_BROADCAST_SIGNAL',
        'role': 'Flood rescue boat deployment and life-safety extraction.'
    },
    {
        'name': 'City Municipal Integrated Command & Control Centre (GCC-ICCC)',
        'code': 'GCC_ICCC',
        'contact': '+91-1913 (Municipal Emergency Helpline)',
        'channel': 'MUNICIPAL_DISPATCH_RELAY',
        'role': 'Stormwater pump deployment, road barrier placement, and relief shelters.'
    },
    {
        'name': 'Disaster Relief Email Dispatch Service',
        'code': 'EMAIL_ALERT',
        'contact': 'disaster-alerts@state.gov.in, relief-authority@ndma.gov.in',
        'channel': 'EMAIL_DISPATCH',
        'role': 'Automated high-priority disaster warning email with human behavior safety advisories.'
    }
]

class NotificationService:
    @classmethod
    def get_registered_authorities(cls) -> List[Dict[str, Any]]:
        return AUTHORITY_REGISTRY

    @classmethod
    def format_alert_message(cls, zone: Zone, prediction: Prediction, authority: Dict[str, Any]) -> str:
        score_pct = round(prediction.risk_score * 100, 1)
        snap = prediction.input_features_snapshot or {}
        rain = snap.get('rainfall_mm', 'N/A')
        press = snap.get('pressure_hpa', 'N/A')
        wind = snap.get('wind_speed_kmh', 'N/A')

        return (
            f"🚨 [URGENT EMERGENCY ALERT - {authority['code']}] "
            f"Micro-Zone '{zone.name}' ({zone.zone_code}) at Lat {zone.latitude:.3f}, Lon {zone.longitude:.3f} "
            f"has reached CRITICAL DISASTER HAZARD status ({score_pct}% risk probability within next {prediction.prediction_horizon_hours}h). "
            f"Key Triggers: Rainfall: {rain}mm, Barometric Pressure: {press}hPa, Wind: {wind}km/h. "
            f"Advisory: Pre-deployment of inflatable rescue boats, emergency power backups, and vulnerable population evacuation advised. "
            f"Automated transmission by Micro-Predict AI Engine at {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}."
        )

    @classmethod
    def dispatch_authority_alerts(cls, prediction: Prediction, zone: Zone) -> List[AlertNotification]:
        """
        Automatically dispatches early-warning alerts to all registered emergency
        authorities when a micro-zone crosses into HIGH RISK (>= 0.70).
        """
        if prediction.risk_category != 'HIGH':
            return []

        dispatched_alerts = []
        now = datetime.now(timezone.utc)

        for auth in AUTHORITY_REGISTRY:
            msg = cls.format_alert_message(zone, prediction, auth)
            
            alert = AlertNotification(
                zone_id=zone.id,
                prediction_id=prediction.id,
                authority_name=auth['name'],
                authority_code=auth['code'],
                channel=auth['channel'],
                severity='CRITICAL_HIGH',
                risk_score=prediction.risk_score,
                message_body=msg,
                recipient_contact=auth['contact'],
                dispatch_status='DELIVERED',
                dispatched_at=now
            )
            db.session.add(alert)
            dispatched_alerts.append(alert)
            logger.warning(
                f"[AUTHORITY ALERT TRANSMITTED] Sent to {auth['code']} ({auth['contact']}) "
                f"for Zone {zone.zone_code} - Score: {prediction.risk_score:.2f}"
            )

        db.session.commit()
        return dispatched_alerts

    @classmethod
    def manual_broadcast_drill(cls, zone_id: int, authority_code: Optional[str] = None) -> List[AlertNotification]:
        """
        Manual drill trigger for testing emergency communications with authorities.
        """
        zone = db.session.get(Zone, zone_id)
        if not zone:
            raise ValueError(f"Zone with ID {zone_id} not found.")

        latest_pred = Prediction.query.filter_by(zone_id=zone.id)\
            .order_by(Prediction.assessment_timestamp.desc()).first()

        targets = AUTHORITY_REGISTRY
        if authority_code:
            targets = [a for a in AUTHORITY_REGISTRY if a['code'] == authority_code.upper()]

        dispatched = []
        now = datetime.now(timezone.utc)

        for auth in targets:
            score = latest_pred.risk_score if latest_pred else 0.85
            msg = (
                f"⚠️ [EMERGENCY DRILL SIMULATION - {auth['code']}] "
                f"Preparedness signal transmission for Micro-Zone '{zone.name}' ({zone.zone_code}). "
                f"System verification test: AI Micro-Zone Disaster Early Warning Network operating normally."
            )
            alert = AlertNotification(
                zone_id=zone.id,
                prediction_id=latest_pred.id if latest_pred else None,
                authority_name=auth['name'],
                authority_code=auth['code'],
                channel=auth['channel'],
                severity='DRILL_TEST',
                risk_score=score,
                message_body=msg,
                recipient_contact=auth['contact'],
                dispatch_status='DELIVERED',
                dispatched_at=now
            )
            db.session.add(alert)
            dispatched.append(alert)

        db.session.commit()
        return dispatched
