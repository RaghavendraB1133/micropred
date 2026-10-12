import json
import urllib.request
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import pandas as pd
from app.extensions import db
from app.models.zone import Zone
from app.models.weather import WeatherObservation
from app.utils.logger import logger

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

class LiveWeatherService:
    @classmethod
    def fetch_live_weather_for_coords(
        cls,
        latitude: float,
        longitude: float,
        past_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Fetches real-time and past 24-hour meteorological observations
        from the free Open-Meteo public API (no API key required).
        """
        params = (
            f"?latitude={latitude}&longitude={longitude}"
            "&hourly=temperature_2m,relative_humidity_2m,precipitation,surface_pressure,wind_speed_10m,soil_moisture_0_to_1cm"
            "&past_days=1&forecast_days=1"
        )
        url = f"{OPEN_METEO_BASE_URL}{params}"
        
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'MicroPredict-Disaster-AI/1.0'}
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            payload = json.loads(response.read().decode('utf-8'))

        hourly = payload.get('hourly', {})
        times = hourly.get('time', [])
        temps = hourly.get('temperature_2m', [])
        humids = hourly.get('relative_humidity_2m', [])
        precips = hourly.get('precipitation', [])
        pressures = hourly.get('surface_pressure', [])
        winds = hourly.get('wind_speed_10m', [])
        soils = hourly.get('soil_moisture_0_to_1cm', [])

        records = []
        for i in range(len(times)):
            t_str = times[i]
            # Parse timestamp
            dt = datetime.fromisoformat(t_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            # Volumetric water content m3/m3 scaled to ~0-100% saturation
            soil_raw = soils[i] if i < len(soils) and soils[i] is not None else 0.25
            soil_pct = round(min(100.0, float(soil_raw) * 200.0), 2)

            records.append({
                'timestamp': dt,
                'rainfall_mm': float(precips[i]) if i < len(precips) and precips[i] is not None else 0.0,
                'temperature_c': float(temps[i]) if i < len(temps) and temps[i] is not None else 25.0,
                'humidity_pct': float(humids[i]) if i < len(humids) and humids[i] is not None else 60.0,
                'wind_speed_kmh': float(winds[i]) if i < len(winds) and winds[i] is not None else 10.0,
                'pressure_hpa': float(pressures[i]) if i < len(pressures) and pressures[i] is not None else 1013.0,
                'soil_moisture_pct': soil_pct,
            })

        # Find current time or take the latest past_hours records up to now
        now_utc = datetime.now(timezone.utc)
        past_records = [r for r in records if r['timestamp'] <= now_utc]
        if len(past_records) >= past_hours:
            return past_records[-past_hours:]
        # Fallback to last past_hours records in the payload
        return records[-past_hours:]

    @classmethod
    def sync_zone_live_weather(cls, zone_id: int) -> Dict[str, Any]:
        """
        Queries live internet weather for a specific zone and persists
        the past 24 hourly observations into the WeatherObservation database.
        """
        zone = db.session.get(Zone, zone_id)
        if not zone:
            raise ValueError(f"Zone with ID {zone_id} not found.")

        try:
            live_records = cls.fetch_live_weather_for_coords(
                latitude=zone.latitude,
                longitude=zone.longitude,
                past_hours=24
            )
        except Exception as e:
            logger.error(f"Failed to fetch live weather for Zone {zone.zone_code}: {str(e)}")
            raise RuntimeError(f"Could not connect to live weather service: {str(e)}")

        new_observations = []
        for r in live_records:
            existing = WeatherObservation.query.filter_by(
                zone_id=zone.id,
                timestamp=r['timestamp']
            ).first()

            if existing:
                existing.rainfall_mm = r['rainfall_mm']
                existing.temperature_c = r['temperature_c']
                existing.humidity_pct = r['humidity_pct']
                existing.wind_speed_kmh = r['wind_speed_kmh']
                existing.pressure_hpa = r['pressure_hpa']
                existing.soil_moisture_pct = r['soil_moisture_pct']
                existing.data_source = f"Live Open-Meteo Weather API ({zone.latitude:.3f}, {zone.longitude:.3f})"
                new_observations.append(existing)
            else:
                obs = WeatherObservation(
                    zone_id=zone.id,
                    timestamp=r['timestamp'],
                    rainfall_mm=r['rainfall_mm'],
                    temperature_c=r['temperature_c'],
                    humidity_pct=r['humidity_pct'],
                    wind_speed_kmh=r['wind_speed_kmh'],
                    pressure_hpa=r['pressure_hpa'],
                    soil_moisture_pct=r['soil_moisture_pct'],
                    data_source=f"Live Open-Meteo Weather API ({zone.latitude:.3f}, {zone.longitude:.3f})"
                )
                db.session.add(obs)
                new_observations.append(obs)

        db.session.commit()
        logger.info(f"Successfully synced {len(new_observations)} live weather hours for {zone.zone_code}")

        latest = live_records[-1] if live_records else {}
        return {
            'zone_id': zone.id,
            'zone_code': zone.zone_code,
            'zone_name': zone.name,
            'synced_hours': len(new_observations),
            'latest_live_conditions': {
                'timestamp': latest.get('timestamp', datetime.now(timezone.utc)).isoformat(),
                'temperature_c': latest.get('temperature_c'),
                'rainfall_mm': latest.get('rainfall_mm'),
                'wind_speed_kmh': latest.get('wind_speed_kmh'),
                'pressure_hpa': latest.get('pressure_hpa'),
                'humidity_pct': latest.get('humidity_pct'),
                'soil_moisture_pct': latest.get('soil_moisture_pct')
            },
            'source': 'Live Open-Meteo Internet Weather API'
        }

    @classmethod
    def sync_all_zones_live_weather(cls) -> List[Dict[str, Any]]:
        """
        Synchronizes live internet weather for all registered active micro-zones.
        """
        zones = Zone.query.filter_by(is_active=True).all()
        results = []
        for zone in zones:
            try:
                res = cls.sync_zone_live_weather(zone.id)
                results.append(res)
            except Exception as e:
                logger.warning(f"Live sync skipped for {zone.zone_code}: {str(e)}")
        return results
