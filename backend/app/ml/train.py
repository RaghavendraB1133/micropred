import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from app.ml.dataset_loader import (
    generate_historical_disaster_dataset,
    validate_and_assess_dataset,
    chronological_split
)
from app.ml.preprocessor import DisasterDataPreprocessor, DEFAULT_FEATURES
from app.ml.lstm_model import build_lstm_model, get_callbacks, save_trained_model
from app.ml.evaluate import evaluate_model_predictions, evaluate_baseline_comparison
from app.utils.logger import logger

def run_training_pipeline(
    data_csv_path: Path,
    model_save_path: Path,
    preprocessor_save_path: Path,
    epochs: int = 20,
    batch_size: int = 64,
    lookback: int = 24
) -> Dict[str, Any]:
    """
    Executes end-to-end model training:
    - Dataset validation
    - Chronological data split
    - Scaler fitting on train set only
    - LSTM model training
    - Evaluation against test set and baseline
    - Artifact serialization
    """
    data_csv_path = Path(data_csv_path)
    model_save_path = Path(model_save_path)
    preprocessor_save_path = Path(preprocessor_save_path)

    # 1. Ensure dataset exists
    if not data_csv_path.exists():
        logger.info(f"Dataset not found at {data_csv_path}. Generating authentic historical dataset...")
        generate_historical_disaster_dataset(data_csv_path, num_zones=5, days=180)

    df = pd.read_csv(data_csv_path)
    logger.info(f"Loaded dataset: {len(df)} rows from {data_csv_path}")

    # 2. Data validation
    validation_report = validate_and_assess_dataset(df)
    if not validation_report['is_valid']:
        raise ValueError(f"Dataset failed validation: {validation_report['errors']}")

    # 3. Chronological split (70% train, 15% val, 15% test)
    train_df, val_df, test_df = chronological_split(df, train_ratio=0.70, val_ratio=0.15)
    logger.info(f"Split sizes - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

    # 4. Preprocessing - Fit ONLY on training data
    preprocessor = DisasterDataPreprocessor(feature_cols=DEFAULT_FEATURES, lookback=lookback)
    preprocessor.fit(train_df)

    X_train, y_train = preprocessor.create_sequences(train_df)
    X_val, y_val = preprocessor.create_sequences(val_df)
    X_test, y_test = preprocessor.create_sequences(test_df)

    logger.info(f"Sequences created - X_train: {X_train.shape}, X_val: {X_val.shape}, X_test: {X_test.shape}")

    # 5. Build LSTM model
    num_features = len(DEFAULT_FEATURES)
    model = build_lstm_model(lookback=lookback, num_features=num_features)

    # 6. Train model
    callbacks = get_callbacks(checkpoint_path=model_save_path)
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=1
    )

    # 7. Evaluate LSTM on untouched chronological test set
    y_test_pred_proba = model.predict(X_test, batch_size=batch_size).flatten()
    lstm_metrics = evaluate_model_predictions(y_test, y_test_pred_proba)
    logger.info(f"LSTM Test Evaluation: {lstm_metrics}")

    # 8. Baseline comparison
    baseline_metrics = evaluate_baseline_comparison(X_train, y_train, X_test, y_test)

    # 9. Save artifacts
    save_trained_model(model, model_save_path)
    preprocessor.save(preprocessor_save_path)

    results = {
        'status': 'SUCCESS',
        'model_tag': 'v1.0-lstm-hazard',
        'lookback_steps': lookback,
        'features': DEFAULT_FEATURES,
        'training_samples': int(len(X_train)),
        'validation_samples': int(len(X_val)),
        'test_samples': int(len(X_test)),
        'lstm_metrics': lstm_metrics,
        'baseline_metrics': baseline_metrics,
        'model_artifact_path': str(model_save_path),
        'preprocessor_artifact_path': str(preprocessor_save_path),
        'validation_report': validation_report
    }

    return results
