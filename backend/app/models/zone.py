from datetime import datetime, timezone
from app.extensions import db

class Zone(db.Model):
    __tablename__ = 'zones'

    id = db.Column(db.Integer, primary_key=True)
    zone_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    radius_km = db.Column(db.Float, default=5.0, nullable=False)
    boundary_coordinates = db.Column(db.JSON, nullable=True)  # Polygon or GeoJSON coordinates
    elevation_m = db.Column(db.Float, nullable=True, default=25.0)
    topography = db.Column(db.String(64), nullable=True, default='Coastal Plain')  # e.g. Coastal, River Basin, Hilly, Urban
    population_estimate = db.Column(db.Integer, nullable=True, default=50000)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    weather_observations = db.relationship('WeatherObservation', backref='zone', lazy='dynamic', cascade='all, delete-orphan')
    disaster_events = db.relationship('DisasterEvent', backref='zone', lazy='dynamic', cascade='all, delete-orphan')
    predictions = db.relationship('Prediction', backref='zone', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'zone_code': self.zone_code,
            'name': self.name,
            'description': self.description,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'radius_km': self.radius_km,
            'boundary_coordinates': self.boundary_coordinates,
            'elevation_m': self.elevation_m,
            'topography': self.topography,
            'population_estimate': self.population_estimate,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
