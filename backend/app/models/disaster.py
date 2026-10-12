from datetime import datetime, timezone
from app.extensions import db

class DisasterEvent(db.Model):
    __tablename__ = 'disaster_events'

    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id', ondelete='CASCADE'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    disaster_type = db.Column(db.String(64), nullable=False)  # e.g., 'Flash Flood', 'Cyclone / Severe Storm', 'Landslide'
    severity_level = db.Column(db.String(32), default='MEDIUM')  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    occurrence_flag = db.Column(db.Integer, default=1, nullable=False)  # 1 for disaster occurrence
    affected_radius_km = db.Column(db.Float, default=5.0)
    description = db.Column(db.Text, nullable=True)
    data_source = db.Column(db.String(128), default='Historical Emergency Record')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.Index('ix_disaster_zone_time', 'zone_id', 'timestamp'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'zone_id': self.zone_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'disaster_type': self.disaster_type,
            'severity_level': self.severity_level,
            'occurrence_flag': self.occurrence_flag,
            'affected_radius_km': self.affected_radius_km,
            'description': self.description,
            'data_source': self.data_source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
