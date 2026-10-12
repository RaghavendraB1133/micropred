from datetime import datetime, timezone
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from flask import current_app

from app.extensions import db
from app.models.zone import Zone
from app.models.weather import WeatherObservation
from app.models.model_version import ModelVersion
from app.models.prediction import Prediction
from app.ml.preprocessor import DisasterDataPreprocessor, DEFAULT_FEATURES
from app.ml.lstm_model import load_trained_model
from app.services.risk_engine import MicroZoneRiskEngine
from app.utils.logger import logger

class PredictionService:
    _model_cache = None
    _preprocessor_cache = None

    @classmethod
    def get_model_and_preprocessor(cls):
        """
        Loads and caches the active LSTM model and preprocessor artifacts.
        """
        model_path = Path(current_app.config['MODEL_PATH'])
        preprocessor_path = Path(current_app.config['PREPROCESSOR_PATH'])

        if not model_path.exists():
            raise FileNotFoundError(
                f"LSTM model artifact not found at {model_path}. "
                "Please run model training pipeline before generating predictions."
            )
        if not preprocessor_path.exists():
            raise FileNotFoundError(
                f"Preprocessor artifact not found at {preprocessor_path}. "
                "Please run model training pipeline before generating predictions."
            )

        if cls._model_cache is None:
            cls._model_cache = load_trained_model(model_path)
        if cls._preprocessor_cache is None:
            cls._preprocessor_cache = DisasterDataPreprocessor.load(preprocessor_path)

        return cls._model_cache, cls._preprocessor_cache

    @classmethod
    def run_prediction_for_zone(cls, zone_id: int, horizon_hours: int = 24) -> Prediction:
        zone = db.session.get(Zone, zone_id)
        if not zone:
            raise ValueError(f"Zone with ID {zone_id} does not exist.")

        model, preprocessor = cls.get_model_and_preprocessor()

        # Query recent observations for this zone
        recent_obs = WeatherObservation.query.filter_by(zone_id=zone.id)\
            .order_by(WeatherObservation.timestamp.desc())\
            .limit(current_app.config['LOOKBACK_STEPS']).all()

        if not recent_obs:
            raise ValueError(
                f"Insufficient historical weather observations for Zone {zone.zone_code}. "
                "At least recent weather data is required to form a time-series sequence."
            )

        # Convert to DataFrame in chronological order
        obs_dicts = [obs.to_dict() for obs in reversed(recent_obs)]
        df_recent = pd.DataFrame(obs_dicts)

        # Ensure all required features are present
        for col in DEFAULT_FEATURES:
            if col not in df_recent.columns:
                df_recent[col] = 0.0

        # Prepare 3D sequence tensor (1, lookback, num_features)
        input_tensor = preprocessor.prepare_inference_sequence(df_recent)

        # Model inference & probability calibration
        raw_pred = model.predict(input_tensor, verbose=0)
        raw_prob = float(raw_pred[0][0])
        risk_score = MicroZoneRiskEngine.calibrate_score(raw_prob)

        # Classification via Risk Engine
        risk_category = MicroZoneRiskEngine.classify(risk_score)

        # Retrieve or link active model version
        active_model_ver = ModelVersion.query.filter_by(is_active=True).first()

        # Snapshot of latest weather features for explainability
        latest_weather = obs_dicts[-1] if obs_dicts else {}
        feature_snapshot = {
            'rainfall_mm': latest_weather.get('rainfall_mm', 0.0),
            'temperature_c': latest_weather.get('temperature_c', 0.0),
            'humidity_pct': latest_weather.get('humidity_pct', 0.0),
            'wind_speed_kmh': latest_weather.get('wind_speed_kmh', 0.0),
            'pressure_hpa': latest_weather.get('pressure_hpa', 0.0),
            'soil_moisture_pct': latest_weather.get('soil_moisture_pct', 0.0),
        }

        prediction = Prediction(
            zone_id=zone.id,
            model_version_id=active_model_ver.id if active_model_ver else None,
            assessment_timestamp=datetime.now(timezone.utc),
            prediction_horizon_hours=horizon_hours,
            prediction_target="Severe Weather / Flash Flood Hazard",
            risk_score=risk_score,
            risk_category=risk_category,
            input_features_snapshot=feature_snapshot,
            source_data_period=f"Last {len(obs_dicts)} historical observation hours",
            limitations_notes=(
                "Academic decision-support estimate based on sequential weather observations. "
                "Human behavioral sensor metrics pending future validated integration. "
                "Not an official emergency notification."
            )
        )

        db.session.add(prediction)
        db.session.commit()
        logger.info(f"Generated prediction for Zone {zone.zone_code}: Score={risk_score:.4f}, Category={risk_category}")

        # Automatically dispatch emergency signals to authorities if HIGH hazard is detected
        if risk_category == 'HIGH':
            from app.services.notification_service import NotificationService
            NotificationService.dispatch_authority_alerts(prediction, zone)

        return prediction

    @classmethod
    def run_batch_predictions(cls) -> List[Prediction]:
        zones = Zone.query.filter_by(is_active=True).all()
        results = []
        for zone in zones:
            try:
                pred = cls.run_prediction_for_zone(zone.id)
                results.append(pred)
            except Exception as e:
                logger.warning(f"Batch prediction skipped for zone {zone.zone_code}: {str(e)}")
        return results

    @classmethod
    def simulate_scenario(cls, scenario_name: str = 'storm_surge') -> List[Prediction]:
        """
        Injects realistic multi-zone meteorological conditions for disaster simulation
        demonstration, and automatically runs the LSTM prediction pipeline.
        """
        from datetime import timedelta
        zones = Zone.query.filter_by(is_active=True).order_by(Zone.id.asc()).all()
        now = datetime.now(timezone.utc)

        scenario_profiles = {
            'storm_surge': [
                {'rain': 85.0, 'temp': 23.5, 'hum': 98.0, 'wind': 85.0, 'press': 978.0, 'soil': 95.0}, # Coast -> HIGH
                {'rain': 52.0, 'temp': 24.0, 'hum': 95.0, 'wind': 60.0, 'press': 986.0, 'soil': 90.0}, # River -> HIGH
                {'rain': 32.0, 'temp': 25.5, 'hum': 88.0, 'wind': 42.0, 'press': 996.0, 'soil': 76.0}, # Urban -> MEDIUM
                {'rain': 12.0, 'temp': 26.0, 'hum': 72.0, 'wind': 22.0, 'press': 1008.0, 'soil': 48.0}, # Hill -> LOW
                {'rain': 15.0, 'temp': 27.0, 'hum': 75.0, 'wind': 26.0, 'press': 1007.0, 'soil': 52.0}, # Harbor -> LOW
            ],
            'flash_flood': [
                {'rain': 95.0, 'temp': 23.0, 'hum': 99.0, 'wind': 70.0, 'press': 975.0, 'soil': 98.0}, # Coast -> HIGH
                {'rain': 88.0, 'temp': 23.0, 'hum': 98.0, 'wind': 68.0, 'press': 976.0, 'soil': 96.0}, # River -> HIGH
                {'rain': 45.0, 'temp': 24.5, 'hum': 92.0, 'wind': 48.0, 'press': 992.0, 'soil': 85.0}, # Urban -> MEDIUM
                {'rain': 38.0, 'temp': 25.0, 'hum': 89.0, 'wind': 40.0, 'press': 995.0, 'soil': 79.0}, # Hill -> MEDIUM
                {'rain': 8.0, 'temp': 27.5, 'hum': 65.0, 'wind': 16.0, 'press': 1012.0, 'soil': 38.0}, # Harbor -> LOW
            ],
            'calm': [
                {'rain': 0.0, 'temp': 28.0, 'hum': 60.0, 'wind': 12.0, 'press': 1013.0, 'soil': 32.0}, # Coast -> LOW
                {'rain': 0.0, 'temp': 28.5, 'hum': 58.0, 'wind': 10.0, 'press': 1014.0, 'soil': 30.0}, # River -> LOW
                {'rain': 0.0, 'temp': 29.0, 'hum': 55.0, 'wind': 8.0, 'press': 1013.5, 'soil': 28.0}, # Urban -> LOW
                {'rain': 0.0, 'temp': 27.0, 'hum': 62.0, 'wind': 14.0, 'press': 1015.0, 'soil': 35.0}, # Hill -> LOW
                {'rain': 2.0, 'temp': 28.0, 'hum': 65.0, 'wind': 15.0, 'press': 1012.5, 'soil': 36.0}, # Harbor -> LOW
            ]
        }

        profiles = scenario_profiles.get(scenario_name, scenario_profiles['storm_surge'])

        for idx, zone in enumerate(zones):
            prof = profiles[idx % len(profiles)]
            for h in range(24):
                ts = now - timedelta(hours=(24 - h))
                factor = 0.5 + 0.5 * (h / 24.0)
                obs = WeatherObservation(
                    zone_id=zone.id,
                    timestamp=ts,
                    rainfall_mm=round(prof['rain'] * factor, 2),
                    temperature_c=round(prof['temp'], 2),
                    humidity_pct=round(min(100.0, prof['hum'] * (0.9 + 0.1 * factor)), 2),
                    wind_speed_kmh=round(prof['wind'] * factor, 2),
                    pressure_hpa=round(prof['press'] + (1.0 - factor) * 8.0, 2),
                    soil_moisture_pct=round(min(100.0, prof['soil'] * factor), 2),
                    data_source=f"Scenario Simulation: {scenario_name.title()}"
                )
                db.session.add(obs)

        db.session.commit()
        return cls.run_batch_predictions()
