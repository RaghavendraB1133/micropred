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

    @classmethod
    def forecast_future_disaster(cls, zone_id: int, horizons: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Generates multi-horizon future disaster forecasts for a micro-zone
        based on sequential historical observations (previous data).
        Evaluates physical meteorological momentum and runs TensorFlow Stacked LSTM inference.
        """
        from datetime import timedelta
        if horizons is None:
            horizons = [6, 12, 18, 24, 36, 48, 72]

        zone = db.session.get(Zone, zone_id)
        if not zone:
            raise ValueError(f"Zone with ID {zone_id} does not exist.")

        model, preprocessor = cls.get_model_and_preprocessor()

        # Query recent observations for this zone
        obs_records = WeatherObservation.query.filter_by(zone_id=zone.id)\
            .order_by(WeatherObservation.timestamp.desc())\
            .limit(48).all()

        if not obs_records:
            raise ValueError(f"No historical weather observations recorded for Zone {zone.zone_code}.")

        obs_dicts = [o.to_dict() for o in reversed(obs_records)]
        total_prev_rain = sum(float(o.get('rainfall_mm', 0.0)) for o in obs_dicts)
        avg_prev_wind = float(np.mean([float(o.get('wind_speed_kmh', 10.0)) for o in obs_dicts]))
        latest_obs = obs_dicts[-1]
        earliest_obs = obs_dicts[0]

        p_delta = float(latest_obs.get('pressure_hpa', 1013.0)) - float(earliest_obs.get('pressure_hpa', 1013.0))
        p_rate = p_delta / max(1, len(obs_dicts))

        latest_ts_raw = latest_obs.get('timestamp')
        if isinstance(latest_ts_raw, str):
            try:
                latest_time = datetime.fromisoformat(latest_ts_raw.replace('Z', '+00:00'))
            except Exception:
                latest_time = datetime.now(timezone.utc)
        elif isinstance(latest_ts_raw, datetime):
            latest_time = latest_ts_raw
        else:
            latest_time = datetime.now(timezone.utc)

        trigger_factors = []
        if total_prev_rain > 50.0:
            trigger_factors.append(f"Heavy cumulative rainfall ({total_prev_rain:.1f} mm) recorded over previous {len(obs_dicts)} observation steps")
        elif total_prev_rain > 15.0:
            trigger_factors.append(f"Moderate cumulative rainfall ({total_prev_rain:.1f} mm) recorded in previous data")

        if p_delta < -8.0:
            trigger_factors.append(f"Rapid barometric pressure depression ({p_delta:.1f} hPa) indicating approaching deep convective storm system")
        elif p_delta < -3.0:
            trigger_factors.append(f"Barometric pressure drop ({p_delta:.1f} hPa) indicating atmospheric instability")

        latest_soil = float(latest_obs.get('soil_moisture_pct', 30.0))
        if latest_soil > 80.0:
            trigger_factors.append(f"Elevated soil saturation level ({latest_soil:.1f}%) critically reducing watershed absorption capacity")

        if avg_prev_wind > 45.0:
            trigger_factors.append(f"High-velocity sustained wind gusts (avg {avg_prev_wind:.1f} km/h)")

        if not trigger_factors:
            trigger_factors.append("Stable baseline meteorological parameters; no severe precursors detected in previous observations")

        # Step stride for historical timeline points
        step_stride = max(1, len(obs_dicts) // 5)
        historical_timeline = []
        for i in range(0, len(obs_dicts), step_stride):
            o = obs_dicts[i]
            ts = o.get('timestamp')
            hours_ago = 0
            if isinstance(ts, str):
                try:
                    t_parsed = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    hours_ago = int((latest_time - t_parsed).total_seconds() / 3600)
                except Exception:
                    hours_ago = (len(obs_dicts) - 1 - i)
            elif isinstance(ts, datetime):
                hours_ago = int((latest_time - ts).total_seconds() / 3600)
            else:
                hours_ago = (len(obs_dicts) - 1 - i)

            # Compute historical baseline score for sequential chart
            rain_val = float(o.get('rainfall_mm', 0.0))
            wind_val = float(o.get('wind_speed_kmh', 10.0))
            soil_val = float(o.get('soil_moisture_pct', 30.0))
            press_val = float(o.get('pressure_hpa', 1013.0))
            raw_hazard = (rain_val / 90.0) * 0.5 + (wind_val / 80.0) * 0.3 + (soil_val / 100.0) * 0.2 + max(0.0, (1013.0 - press_val) / 30.0) * 0.3
            hist_calib = MicroZoneRiskEngine.calibrate_score(min(0.98, raw_hazard))
            hist_pct = round(hist_calib * 100.0, 1)

            label = "NOW" if i == len(obs_dicts) - 1 else f"-{abs(hours_ago)}h"
            historical_timeline.append({
                'label': label,
                'timestamp': ts,
                'rainfall_mm': round(rain_val, 1),
                'wind_speed_kmh': round(wind_val, 1),
                'pressure_hpa': round(press_val, 1),
                'soil_moisture_pct': round(soil_val, 1),
                'risk_score_pct': hist_pct,
                'is_future': False
            })

        future_forecasts = []
        is_active_storm = float(latest_obs.get('rainfall_mm', 0.0)) > 15.0 or float(latest_obs.get('pressure_hpa', 1013.0)) < 1000.0 or float(latest_obs.get('wind_speed_kmh', 0.0)) > 35.0

        for h in horizons:
            proj_time = latest_time + timedelta(hours=h)
            if is_active_storm:
                if h <= 18:
                    curve_factor = 1.0 + (h / 18.0) * 0.35
                elif h <= 36:
                    curve_factor = 1.35 - ((h - 18) / 18.0) * 0.45
                else:
                    curve_factor = max(0.2, 0.90 - ((h - 36) / 36.0) * 0.70)
            else:
                curve_factor = 0.95 + 0.1 * np.sin(h * np.pi / 12.0)

            sim_seq = []
            for step in range(24):
                step_h = h - (24 - step)
                sim_step_time = latest_time + timedelta(hours=step_h)
                if step_h <= 0 and (len(obs_dicts) + step_h - 1) >= 0:
                    base = obs_dicts[max(0, len(obs_dicts) + step_h - 1)]
                    sim_seq.append({
                        'timestamp': base.get('timestamp', sim_step_time.isoformat()),
                        'rainfall_mm': float(base.get('rainfall_mm', 0.0)),
                        'temperature_c': float(base.get('temperature_c', 25.0)),
                        'humidity_pct': float(base.get('humidity_pct', 60.0)),
                        'wind_speed_kmh': float(base.get('wind_speed_kmh', 10.0)),
                        'pressure_hpa': float(base.get('pressure_hpa', 1013.0)),
                        'soil_moisture_pct': float(base.get('soil_moisture_pct', 30.0))
                    })
                else:
                    step_factor = curve_factor if step_h > 0 else 1.0
                    rain = round(max(0.0, float(latest_obs.get('rainfall_mm', 0.0)) * step_factor), 2)
                    wind = round(max(5.0, float(latest_obs.get('wind_speed_kmh', 10.0)) * step_factor), 2)
                    hum = round(min(100.0, max(40.0, float(latest_obs.get('humidity_pct', 60.0)) * (0.95 + 0.05 * step_factor))), 1)
                    press = round(max(960.0, min(1025.0, float(latest_obs.get('pressure_hpa', 1013.0)) - (step_factor - 1.0) * 8.0)), 2)
                    soil = round(min(100.0, max(10.0, float(latest_obs.get('soil_moisture_pct', 30.0)) + (step_factor - 1.0) * 5.0)), 1)
                    temp = round(float(latest_obs.get('temperature_c', 26.0)) - (step_factor - 1.0) * 1.5, 1)
                    sim_seq.append({
                        'timestamp': sim_step_time.isoformat(),
                        'rainfall_mm': rain,
                        'temperature_c': temp,
                        'humidity_pct': hum,
                        'wind_speed_kmh': wind,
                        'pressure_hpa': press,
                        'soil_moisture_pct': soil
                    })

            df_sim = pd.DataFrame(sim_seq)
            input_tensor = preprocessor.prepare_inference_sequence(df_sim)
            raw_pred = model.predict(input_tensor, verbose=0)
            raw_prob = float(raw_pred[0][0])
            risk_score = MicroZoneRiskEngine.calibrate_score(raw_prob)
            category = MicroZoneRiskEngine.classify(risk_score)

            last_step = sim_seq[-1]
            if category == 'HIGH':
                if last_step['rainfall_mm'] >= 30.0 or last_step['soil_moisture_pct'] >= 80.0:
                    disaster_name = "Severe Flash Flood & Inundation Surge"
                    advisory = "Critical inundation threat. Activate flood barriers and deploy NDRF rescue craft to vulnerable lowlands."
                elif last_step['wind_speed_kmh'] >= 50.0:
                    disaster_name = "High-Intensity Cyclonic Gale & Storm Surge"
                    advisory = "Severe gale advisory. Halt maritime departures, secure power infrastructure, and enforce coastal setbacks."
                else:
                    disaster_name = "Critical Multi-Hazard Weather Inundation"
                    advisory = "Emergency command center standby. Pre-position medical and relief convoys."
            elif category == 'MEDIUM':
                disaster_name = "Elevated Hydro-Meteorological Hazard Advisory"
                advisory = "Heightened runoff alert. Inspect drainage culverts, clear sediment catchments, and issue local travel warnings."
            else:
                disaster_name = "Sub-threshold / Normal Meteorological Baseline"
                advisory = "Routine ambient monitoring. Atmospheric indicators remain well within safe thresholds."

            future_forecasts.append({
                'horizon_hours': h,
                'projected_timestamp': proj_time.isoformat(),
                'time_label': f"+{h}h",
                'risk_score': risk_score,
                'risk_category': category,
                'predicted_disaster': disaster_name,
                'early_warning_advisory': advisory,
                'projected_rainfall_mm': round(last_step['rainfall_mm'], 1),
                'projected_wind_kmh': round(last_step['wind_speed_kmh'], 1),
                'projected_pressure_hpa': round(last_step['pressure_hpa'], 1),
                'projected_soil_moisture_pct': round(last_step['soil_moisture_pct'], 1),
                'confidence_pct': round(float(85.0 + (1.0 - abs(risk_score - 0.5)) * 14.0), 1),
                'is_future': True
            })

        max_pred = max(future_forecasts, key=lambda x: x['risk_score'])
        overall_tier = max_pred['risk_category']
        peak_horizon = max_pred['horizon_hours']

        # Unified combined timeline for charts
        combined_timeline = []
        for h_point in historical_timeline:
            combined_timeline.append({
                'label': h_point['label'],
                'timestamp': h_point['timestamp'],
                'rainfall_mm': h_point['rainfall_mm'],
                'wind_speed_kmh': h_point['wind_speed_kmh'],
                'pressure_hpa': h_point['pressure_hpa'],
                'soil_moisture_pct': h_point['soil_moisture_pct'],
                'risk_score_pct': h_point['risk_score_pct'],
                'future_risk_pct': None,
                'is_future': False
            })

        # NOW Anchor point
        now_risk_pct = round(float(future_forecasts[0]['risk_score'] * 100), 1)
        combined_timeline.append({
            'label': 'NOW (T0)',
            'timestamp': latest_time.isoformat(),
            'rainfall_mm': round(float(latest_obs.get('rainfall_mm', 0.0)), 1),
            'wind_speed_kmh': round(float(latest_obs.get('wind_speed_kmh', 0.0)), 1),
            'pressure_hpa': round(float(latest_obs.get('pressure_hpa', 1013.0)), 1),
            'soil_moisture_pct': round(float(latest_obs.get('soil_moisture_pct', 30.0)), 1),
            'risk_score_pct': now_risk_pct,
            'future_risk_pct': now_risk_pct,
            'is_future': False
        })

        for f_point in future_forecasts:
            combined_timeline.append({
                'label': f_point['time_label'],
                'timestamp': f_point['projected_timestamp'],
                'rainfall_mm': f_point['projected_rainfall_mm'],
                'wind_speed_kmh': f_point['projected_wind_kmh'],
                'pressure_hpa': f_point['projected_pressure_hpa'],
                'soil_moisture_pct': f_point['projected_soil_moisture_pct'],
                'risk_score_pct': None,
                'future_risk_pct': round(float(f_point['risk_score'] * 100), 1),
                'risk_category': f_point['risk_category'],
                'predicted_disaster': f_point['predicted_disaster'],
                'is_future': True
            })

        return {
            'zone': zone.to_dict(),
            'historical_summary': {
                'observations_count': len(obs_dicts),
                'observation_window_label': f"Previous {len(obs_dicts)} Hours of Sequential Data",
                'total_rainfall_mm': round(total_prev_rain, 1),
                'average_wind_kmh': round(avg_prev_wind, 1),
                'latest_pressure_hpa': round(float(latest_obs.get('pressure_hpa', 1013.0)), 1),
                'pressure_trend_delta': round(p_delta, 1),
                'soil_saturation_pct': round(latest_soil, 1),
                'trend_pattern': 'Active Storm Front' if is_active_storm else 'Calm Baseline',
            },
            'trigger_factors': trigger_factors,
            'peak_hazard_window': f"+{peak_horizon}h Ahead ({max_pred['predicted_disaster']})",
            'peak_risk_score': max_pred['risk_score'],
            'overall_future_tier': overall_tier,
            'future_forecasts': future_forecasts,
            'combined_timeline': combined_timeline,
            'scientific_methodology': (
                "Autoregressive meteorological projection combined with TensorFlow Stacked LSTM sequential feature inference. "
                "Calculates future disaster probability curves directly from the historical observation gradient."
            )
        }

