from datetime import datetime, timezone
from app.extensions import db

class Prediction(db.Model):
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id', ondelete='CASCADE'), nullable=False, index=True)
    model_version_id = db.Column(db.Integer, db.ForeignKey('model_versions.id', ondelete='SET NULL'), nullable=True, index=True)
    assessment_timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    prediction_horizon_hours = db.Column(db.Integer, default=24, nullable=False)
    prediction_target = db.Column(db.String(64), default='Severe Weather / Flash Flood Hazard', nullable=False)
    
    # Model quantitative score (calibrated likelihood estimate: 0.0 to 1.0)
    risk_score = db.Column(db.Float, nullable=False)
    
    # Risk category strictly: 'LOW', 'MEDIUM', 'HIGH'
    risk_category = db.Column(db.String(16), nullable=False, index=True)
    
    # Feature values used at inference
    input_features_snapshot = db.Column(db.JSON, nullable=True)
    source_data_period = db.Column(db.String(128), nullable=True)
    
    # Scientific honesty & academic decision-support disclaimers
    limitations_notes = db.Column(db.Text, default=(
        "Academic decision-support estimate based on historical meteorological features. "
        "Behavioral sensor features are pending future validated integration. "
        "Not an official governmental emergency warning."
    ))
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.Index('ix_prediction_zone_time', 'zone_id', 'assessment_timestamp'),
        db.Index('ix_prediction_category', 'risk_category'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'zone_id': self.zone_id,
            'zone_code': self.zone.zone_code if self.zone else None,
            'zone_name': self.zone.name if self.zone else None,
            'latitude': self.zone.latitude if self.zone else None,
            'longitude': self.zone.longitude if self.zone else None,
            'model_version_id': self.model_version_id,
            'model_tag': self.model_version.version_tag if self.model_version else 'v1.0-lstm-baseline',
            'assessment_timestamp': self.assessment_timestamp.isoformat() if self.assessment_timestamp else None,
            'prediction_horizon_hours': self.prediction_horizon_hours,
            'prediction_target': self.prediction_target,
            'risk_score': round(float(self.risk_score), 4),
            'risk_category': self.risk_category,
            'input_features_snapshot': self.input_features_snapshot,
            'source_data_period': self.source_data_period,
            'limitations_notes': self.limitations_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
