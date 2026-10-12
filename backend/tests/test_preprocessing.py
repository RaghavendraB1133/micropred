import pandas as pd
import numpy as np
from app.ml.preprocessor import DisasterDataPreprocessor, DEFAULT_FEATURES
from app.ml.dataset_loader import validate_and_assess_dataset, chronological_split

def test_dataset_validation_good_data():
    df = pd.DataFrame({
        'timestamp': ['2026-01-01 00:00:00', '2026-01-01 01:00:00'],
        'zone_code': ['Z1', 'Z1'],
        'latitude': [13.0, 13.0],
        'longitude': [80.0, 80.0],
        'rainfall_mm': [0.0, 10.0],
        'temperature_c': [25.0, 26.0],
        'humidity_pct': [60.0, 70.0],
        'wind_speed_kmh': [10.0, 12.0],
        'pressure_hpa': [1013.0, 1012.0],
        'soil_moisture_pct': [30.0, 35.0],
        'disaster_occurrence': [0, 0]
    })
    report = validate_and_assess_dataset(df)
    assert report['is_valid'] is True
    assert len(report['missing_required_columns']) == 0

def test_dataset_validation_missing_columns():
    df = pd.DataFrame({
        'timestamp': ['2026-01-01 00:00:00'],
        'rainfall_mm': [0.0]
    })
    report = validate_and_assess_dataset(df)
    assert report['is_valid'] is False
    assert len(report['missing_required_columns']) > 0

def test_preprocessor_fitting_and_sequences():
    # Create sample time series
    rows = []
    for i in range(50):
        rows.append({
            'timestamp': f"2026-01-01 {i % 24:02d}:00:00",
            'rainfall_mm': float(i),
            'temperature_c': 25.0 + (i % 5),
            'humidity_pct': 70.0,
            'wind_speed_kmh': 15.0,
            'pressure_hpa': 1010.0,
            'soil_moisture_pct': 40.0,
            'disaster_occurrence': 1 if i > 35 else 0
        })
    df = pd.DataFrame(rows)

    preprocessor = DisasterDataPreprocessor(feature_cols=DEFAULT_FEATURES, lookback=24)
    preprocessor.fit(df)
    assert preprocessor.is_fitted is True

    X, y = preprocessor.create_sequences(df)
    assert len(X) == 50 - 24
    assert X.shape == (26, 24, 6)
    assert len(y) == 26
