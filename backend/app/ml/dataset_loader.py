import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta
from app.utils.logger import logger

def generate_historical_disaster_dataset(
    output_path: Path,
    num_zones: int = 5,
    days: int = 180,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates realistic historical meteorological time-series with grounded physical correlations:
    high rainfall + low atmospheric pressure + saturated soil moisture -> disaster hazard event.
    """
    np.random.seed(seed)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    zone_profiles = [
        {"code": "Z-COAST-01", "name": "Coastal Lowland Sector A", "lat": 13.0827, "lon": 80.2707, "risk_bias": 1.2},
        {"code": "Z-RIVER-02", "name": "River Basin North", "lat": 13.1250, "lon": 80.2150, "risk_bias": 1.4},
        {"code": "Z-URBAN-03", "name": "Central Urban Metro", "lat": 13.0500, "lon": 80.2400, "risk_bias": 0.9},
        {"code": "Z-HILL-04",  "name": "West Foothills Zone", "lat": 13.0100, "lon": 80.1800, "risk_bias": 0.8},
        {"code": "Z-HARBOR-05","name": "Eastern Port Industrial Area", "lat": 13.1000, "lon": 80.2900, "risk_bias": 1.1},
    ][:num_zones]

    start_date = datetime(2025, 1, 1, 0, 0, 0)
    total_hours = days * 24

    records = []

    for zone in zone_profiles:
        # Base climate parameters
        base_temp = 28.0
        base_pressure = 1012.0
        base_soil = 35.0

        soil_moisture = base_soil
        storm_active = False
        storm_counter = 0

        for h in range(total_hours):
            current_time = start_date + timedelta(hours=h)

            # Diurnal temperature cycle
            hour_of_day = current_time.hour
            temp_variation = 4.0 * np.sin(2 * np.pi * (hour_of_day - 9) / 24)
            temp = base_temp + temp_variation + np.random.normal(0, 1.0)

            # Seasonal/random storm episodic generation
            if not storm_active:
                # 3% chance of entering storm conditions
                if np.random.rand() < (0.015 * zone["risk_bias"]):
                    storm_active = True
                    storm_counter = np.random.randint(12, 48)  # Storm lasts 12 to 48 hours
            
            if storm_active:
                rainfall = float(np.clip(np.random.gamma(shape=3.5, scale=8.0) * zone["risk_bias"], 5.0, 120.0))
                humidity = float(np.clip(np.random.normal(92, 4), 80, 100))
                wind_speed = float(np.clip(np.random.normal(45, 12) * zone["risk_bias"], 20, 110))
                pressure = float(np.clip(base_pressure - np.random.uniform(15, 35), 975, 1005))
                soil_moisture = float(np.clip(soil_moisture + (rainfall * 0.4), 20, 98))
                storm_counter -= 1
                if storm_counter <= 0:
                    storm_active = False
            else:
                # Fair or mild weather
                rainfall = float(np.clip(np.random.exponential(scale=0.8), 0.0, 12.0) if np.random.rand() < 0.1 else 0.0)
                humidity = float(np.clip(np.random.normal(68, 8), 40, 85))
                wind_speed = float(np.clip(np.random.normal(14, 5), 2, 35))
                pressure = float(np.clip(base_pressure + np.random.normal(0, 3), 1005, 1022))
                soil_moisture = float(np.clip(soil_moisture - 0.2 + (rainfall * 0.2), 15, 60))

            # Disaster ground truth definition:
            # Extreme rainfall > 45mm OR (rainfall > 25mm AND soil_moisture > 75%) OR (wind > 75km/h AND pressure < 995hPa)
            is_disaster = 1 if (
                (rainfall > 45.0) or
                (rainfall > 25.0 and soil_moisture > 75.0) or
                (wind_speed > 75.0 and pressure < 995.0)
            ) else 0

            disaster_type = "None"
            if is_disaster:
                if rainfall > 40.0 or soil_moisture > 80.0:
                    disaster_type = "Flash Flood"
                elif wind_speed > 70.0:
                    disaster_type = "Cyclone / Severe Storm"
                else:
                    disaster_type = "Severe Weather Hazard"

            records.append({
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "zone_code": zone["code"],
                "zone_name": zone["name"],
                "latitude": zone["lat"],
                "longitude": zone["lon"],
                "rainfall_mm": round(rainfall, 2),
                "temperature_c": round(temp, 2),
                "humidity_pct": round(humidity, 2),
                "wind_speed_kmh": round(wind_speed, 2),
                "pressure_hpa": round(pressure, 2),
                "soil_moisture_pct": round(soil_moisture, 2),
                "disaster_occurrence": is_disaster,
                "disaster_type": disaster_type
            })

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    logger.info(f"Generated historical dataset with {len(df)} records saved to {output_path}")
    return df

def validate_and_assess_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates CSV dataset integrity and calculates comprehensive data quality metrics.
    """
    required_cols = [
        'timestamp', 'zone_code', 'latitude', 'longitude',
        'rainfall_mm', 'temperature_c', 'humidity_pct',
        'wind_speed_kmh', 'pressure_hpa', 'soil_moisture_pct',
        'disaster_occurrence'
    ]

    missing_cols = [col for col in required_cols if col not in df.columns]
    
    warnings = []
    errors = []

    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")

    # Null analysis
    null_pcts = (df.isnull().mean() * 100).round(2).to_dict()
    high_null_cols = [col for col, pct in null_pcts.items() if pct > 20.0]
    if high_null_cols:
        warnings.append(f"Columns with high null percentages (>20%): {', '.join(high_null_cols)}")

    # Duplicate rows
    duplicate_count = int(df.duplicated(subset=['zone_code', 'timestamp'] if 'zone_code' in df.columns and 'timestamp' in df.columns else None).sum())
    if duplicate_count > 0:
        warnings.append(f"Detected {duplicate_count} duplicate timestamp records for zone.")

    # Coordinate validation
    coord_bounds = {}
    if 'latitude' in df.columns and 'longitude' in df.columns:
        lat_min, lat_max = float(df['latitude'].min()), float(df['latitude'].max())
        lon_min, lon_max = float(df['longitude'].min()), float(df['longitude'].max())
        coord_bounds = {'lat_min': lat_min, 'lat_max': lat_max, 'lon_min': lon_min, 'lon_max': lon_max}
        if lat_min < -90 or lat_max > 90 or lon_min < -180 or lon_max > 180:
            errors.append("Latitude or longitude values exceed physical geospatial boundaries.")

    # Timestamp continuity
    date_start = None
    date_end = None
    if 'timestamp' in df.columns:
        try:
            ts_series = pd.to_datetime(df['timestamp'])
            date_start = ts_series.min().isoformat()
            date_end = ts_series.max().isoformat()
        except Exception as e:
            errors.append(f"Failed to parse timestamp column: {str(e)}")

    return {
        'is_valid': len(errors) == 0,
        'total_rows': len(df),
        'detected_columns': list(df.columns),
        'missing_required_columns': missing_cols,
        'missing_value_percentages': null_pcts,
        'duplicate_rows_count': duplicate_count,
        'date_range_start': date_start,
        'date_range_end': date_end,
        'coordinate_bounds': coord_bounds,
        'disaster_occurrence_rate': float(round(df['disaster_occurrence'].mean() * 100, 2)) if 'disaster_occurrence' in df.columns else None,
        'warnings': warnings,
        'errors': errors
    }

def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Performs strictly chronological train/validation/test split per zone without temporal leakage.
    """
    train_dfs, val_dfs, test_dfs = [], [], []

    for _, group in df.groupby('zone_code'):
        sorted_group = group.sort_values(by='timestamp').reset_index(drop=True)
        n = len(sorted_group)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_dfs.append(sorted_group.iloc[:train_end])
        val_dfs.append(sorted_group.iloc[train_end:val_end])
        test_dfs.append(sorted_group.iloc[val_end:])

    train_df = pd.concat(train_dfs, ignore_index=True)
    val_df = pd.concat(val_dfs, ignore_index=True)
    test_df = pd.concat(test_dfs, ignore_index=True)

    return train_df, val_df, test_df
