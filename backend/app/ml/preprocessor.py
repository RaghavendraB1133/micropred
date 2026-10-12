import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib
from pathlib import Path
from typing import Tuple, List, Optional
from app.utils.logger import logger

DEFAULT_FEATURES = [
    'rainfall_mm',
    'temperature_c',
    'humidity_pct',
    'wind_speed_kmh',
    'pressure_hpa',
    'soil_moisture_pct'
]

class DisasterDataPreprocessor:
    def __init__(self, feature_cols: Optional[List[str]] = None, lookback: int = 24):
        self.feature_cols = feature_cols or DEFAULT_FEATURES
        self.lookback = lookback
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.is_fitted = False

    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        for col in self.feature_cols:
            if col not in df.columns:
                errors.append(f"Missing required feature column: '{col}'")
        if 'disaster_occurrence' not in df.columns:
            errors.append("Missing target column: 'disaster_occurrence'")
        if 'timestamp' not in df.columns:
            errors.append("Missing time column: 'timestamp'")
        return len(errors) == 0, errors

    def clean_and_prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        clean_df = df.copy()
        clean_df['timestamp'] = pd.to_datetime(clean_df['timestamp'], format='mixed', errors='coerce')
        clean_df = clean_df.sort_values(by='timestamp').reset_index(drop=True)
        
        # Numeric coercion
        for col in self.feature_cols:
            clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce')
            clean_df[col] = clean_df[col].ffill().bfill().fillna(0.0)

        if 'disaster_occurrence' in clean_df.columns:
            clean_df['disaster_occurrence'] = pd.to_numeric(clean_df['disaster_occurrence'], errors='coerce').fillna(0).astype(int)

        return clean_df

    def fit(self, df: pd.DataFrame):
        clean_df = self.clean_and_prepare(df)
        self.scaler.fit(clean_df[self.feature_cols])
        self.is_fitted = True
        return self

    def transform_features(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted before calling transform_features")
        clean_df = self.clean_and_prepare(df)
        scaled_features = self.scaler.transform(clean_df[self.feature_cols])
        return scaled_features

    def create_sequences(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        clean_df = self.clean_and_prepare(df)
        scaled_features = self.transform_features(clean_df)
        targets = clean_df['disaster_occurrence'].values

        X, y = [], []
        n_samples = len(scaled_features)
        for i in range(self.lookback, n_samples):
            X.append(scaled_features[i - self.lookback : i])
            y.append(targets[i])

        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    def prepare_inference_sequence(self, recent_df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Preprocessor is not fitted")
        clean_df = self.clean_and_prepare(recent_df)
        if len(clean_df) < self.lookback:
            # Pad with earliest available observation if less than lookback
            pad_needed = self.lookback - len(clean_df)
            pad_rows = pd.concat([clean_df.iloc[[0]]] * pad_needed, ignore_index=True)
            clean_df = pd.concat([pad_rows, clean_df], ignore_index=True)
        
        # Take the most recent lookback rows
        recent_window = clean_df.iloc[-self.lookback:]
        scaled = self.scaler.transform(recent_window[self.feature_cols])
        # Reshape to (1, lookback, num_features)
        return np.expand_dims(scaled, axis=0).astype(np.float32)

    def save(self, filepath: Path):
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            'scaler': self.scaler,
            'feature_cols': self.feature_cols,
            'lookback': self.lookback,
            'is_fitted': self.is_fitted
        }, filepath)
        logger.info(f"Saved preprocessing artifacts to {filepath}")

    @classmethod
    def load(cls, filepath: Path) -> 'DisasterDataPreprocessor':
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Preprocessor file not found at: {filepath}")
        data = joblib.load(filepath)
        preprocessor = cls(feature_cols=data['feature_cols'], lookback=data['lookback'])
        preprocessor.scaler = data['scaler']
        preprocessor.is_fitted = data['is_fitted']
        return preprocessor
