from datetime import datetime, timezone
from app.extensions import db
from app.models.zone import Zone
from app.models.weather import WeatherObservation
from app.models.disaster import DisasterEvent
from app.models.prediction import Prediction
from app.models.dataset import DatasetMetadata

def test_zone_creation_and_to_dict(app):
    with app.app_context():
        zone = Zone(
            zone_code="Z-TEST-99",
            name="North Sector",
            latitude=13.100,
            longitude=80.200,
            radius_km=4.5,
            is_active=True
        )
        db.session.add(zone)
        db.session.commit()

        assert zone.id is not None
        d = zone.to_dict()
        assert d['zone_code'] == "Z-TEST-99"
        assert d['latitude'] == 13.100

def test_weather_observation_creation(app, sample_zone):
    with app.app_context():
        obs = WeatherObservation(
            zone_id=sample_zone.id,
            timestamp=datetime.now(timezone.utc),
            rainfall_mm=35.0,
            temperature_c=28.5,
            humidity_pct=90.0,
            wind_speed_kmh=45.0,
            pressure_hpa=1002.0,
            soil_moisture_pct=80.0
        )
        db.session.add(obs)
        db.session.commit()

        assert obs.id is not None
        assert obs.zone.zone_code == sample_zone.zone_code

def test_prediction_creation_and_fields(app, sample_zone):
    with app.app_context():
        pred = Prediction(
            zone_id=sample_zone.id,
            risk_score=0.78,
            risk_category="HIGH",
            prediction_horizon_hours=24,
            prediction_target="Flash Flood Hazard",
            input_features_snapshot={"rainfall_mm": 55.0}
        )
        db.session.add(pred)
        db.session.commit()

        assert pred.id is not None
        d = pred.to_dict()
        assert d['risk_category'] == 'HIGH'
        assert d['risk_score'] == 0.78
        assert 'limitations_notes' in d
