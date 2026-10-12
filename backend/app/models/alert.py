from datetime import datetime, timezone
from app.extensions import db

class AlertNotification(db.Model):
    __tablename__ = 'alert_notifications'

    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id', ondelete='CASCADE'), nullable=False, index=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey('predictions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    authority_name = db.Column(db.String(128), nullable=False)   # e.g., 'District Disaster Management Authority (DDMA)'
    authority_code = db.Column(db.String(32), nullable=False)   # e.g., 'DDMA', 'NDRF', 'SEOC', 'GCC_ICCC'
    channel = db.Column(db.String(64), nullable=False, default='EMERGENCY_SMS_GATEWAY') # 'SMS_GATEWAY', 'SEOC_DISPATCH_WEBHOOK', 'RADIO_BROADCAST'
    severity = db.Column(db.String(32), nullable=False, default='CRITICAL_HIGH')
    
    risk_score = db.Column(db.Float, nullable=False)
    message_body = db.Column(db.Text, nullable=False)
    recipient_contact = db.Column(db.String(128), nullable=False) # e.g., '+91-1070 Emergency Control'
    
    dispatch_status = db.Column(db.String(32), default='DELIVERED', nullable=False) # 'SENT', 'DELIVERED', 'ACKNOWLEDGED'
    dispatched_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationship
    zone = db.relationship('Zone', backref='alerts', lazy=True)
    prediction = db.relationship('Prediction', backref='alerts', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'zone_id': self.zone_id,
            'zone_code': self.zone.zone_code if self.zone else None,
            'zone_name': self.zone.name if self.zone else None,
            'prediction_id': self.prediction_id,
            'authority_name': self.authority_name,
            'authority_code': self.authority_code,
            'channel': self.channel,
            'severity': self.severity,
            'risk_score': round(float(self.risk_score), 4),
            'message_body': self.message_body,
            'recipient_contact': self.recipient_contact,
            'dispatch_status': self.dispatch_status,
            'dispatched_at': self.dispatched_at.isoformat() if self.dispatched_at else None,
        }
