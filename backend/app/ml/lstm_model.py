import os
# Suppress TF oneDNN info logs for clean terminal output
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from pathlib import Path
from typing import Dict, Any, Optional
from app.utils.logger import logger

def build_lstm_model(lookback: int = 24, num_features: int = 6) -> Sequential:
    """
    Constructs a stacked LSTM neural network for micro-zone disaster risk forecasting.
    """
    model = Sequential([
        Input(shape=(lookback, num_features)),
        LSTM(64, return_sequences=True, name="lstm_layer_1"),
        Dropout(0.2, name="dropout_1"),
        LSTM(32, return_sequences=False, name="lstm_layer_2"),
        Dropout(0.2, name="dropout_2"),
        Dense(16, activation="relu", name="dense_feature_fusion"),
        Dense(1, activation="sigmoid", name="disaster_risk_output")
    ], name="micro_zone_lstm_disaster_predictor")

    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
            tf.keras.metrics.AUC(name="auc")
        ]
    )
    return model

def get_callbacks(checkpoint_path: Optional[Path] = None):
    callbacks = [
        EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
            verbose=1
        )
    ]
    if checkpoint_path:
        checkpoint_path = Path(checkpoint_path)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        callbacks.append(
            ModelCheckpoint(
                filepath=str(checkpoint_path),
                monitor="val_loss",
                save_best_only=True,
                verbose=1
            )
        )
    return callbacks

def save_trained_model(model: Sequential, filepath: Path):
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(filepath))
    logger.info(f"Saved trained LSTM model to {filepath}")

def load_trained_model(filepath: Path) -> Sequential:
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Model artifact not found at: {filepath}")
    model = load_model(str(filepath))
    logger.info(f"Loaded trained LSTM model from {filepath}")
    return model
