import pytest
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db
from app.models.zone import Zone
from app.models.weather import WeatherObservation
from app.models.model_version import ModelVersion
from app.models.prediction import Prediction

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def sample_zone(app):
    zone = Zone(
        zone_code="TEST-ZONE-01",
        name="Test Coastal District",
        description="Zone for unit testing",
        latitude=13.0827,
        longitude=80.2707,
        radius_km=5.0,
        elevation_m=15.0,
        topography="Coastal Plain",
        population_estimate=45000,
        is_active=True
    )
    db.session.add(zone)
    db.session.commit()
    return zone

@pytest.fixture
def sample_weather(app, sample_zone):
    observations = []
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    for i in range(25):
        obs = WeatherObservation(
            zone_id=sample_zone.id,
            timestamp=base_time + timedelta(hours=i),
            rainfall_mm=12.5 + i,
            temperature_c=27.0,
            humidity_pct=85.0,
            wind_speed_kmh=22.0,
            pressure_hpa=1005.0,
            soil_moisture_pct=65.0,
            data_source="Test Station"
        )
        observations.append(obs)
    db.session.bulk_save_objects(observations)
    db.session.commit()
    return observations

@pytest.fixture
def sample_model_version(app):
    m = ModelVersion(
        version_tag="v1.0-test",
        model_name="Test LSTM Model",
        framework="TensorFlow Keras",
        evaluation_metrics={"accuracy": 0.88, "roc_auc": 0.85, "f1_score": 0.82},
        artifact_path="test_artifacts/model.keras",
        preprocessor_path="test_artifacts/prep.joblib",
        features_used=["rainfall_mm", "temperature_c"],
        lookback_steps=24,
        forecast_horizon_hours=24,
        is_active=True
    )
    db.session.add(m)
    db.session.commit()
    return m
