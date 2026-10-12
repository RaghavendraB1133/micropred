from datetime import datetime, timezone
from app.extensions import db

class WeatherObservation(db.Model):
    __tablename__ = 'weather_observations'

    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id', ondelete='CASCADE'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    rainfall_mm = db.Column(db.Float, nullable=False, default=0.0)
    temperature_c = db.Column(db.Float, nullable=False, default=25.0)
    humidity_pct = db.Column(db.Float, nullable=False, default=60.0)
    wind_speed_kmh = db.Column(db.Float, nullable=False, default=10.0)
    pressure_hpa = db.Column(db.Float, nullable=False, default=1013.25)
    soil_moisture_pct = db.Column(db.Float, nullable=False, default=30.0)
    data_source = db.Column(db.String(64), default='Historical Station Data')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('zone_id', 'timestamp', name='uq_zone_timestamp'),
        db.Index('ix_weather_zone_time', 'zone_id', 'timestamp'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'zone_id': self.zone_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'rainfall_mm': self.rainfall_mm,
            'temperature_c': self.temperature_c,
            'humidity_pct': self.humidity_pct,
            'wind_speed_kmh': self.wind_speed_kmh,
            'pressure_hpa': self.pressure_hpa,
            'soil_moisture_pct': self.soil_moisture_pct,
            'data_source': self.data_source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
