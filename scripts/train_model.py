import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from app import create_app
from app.extensions import db
from app.models.model_version import ModelVersion
from app.ml.train import run_training_pipeline
from app.utils.logger import logger

def main():
    app = create_app('development')
    with app.app_context():
        # Ensure tables exist
        db.create_all()

        data_csv_path = app.config['RAW_DATA_DIR'] / 'historical_disaster_weather.csv'
        model_save_path = app.config['MODEL_PATH']
        preprocessor_save_path = app.config['PREPROCESSOR_PATH']

        print("=" * 70)
        print("STARTING GENUINE LSTM DISASTER MODEL TRAINING PIPELINE")
        print("=" * 70)
        print(f"Dataset path:      {data_csv_path}")
        print(f"Model output:      {model_save_path}")
        print(f"Preprocessor path: {preprocessor_save_path}")
        print("-" * 70)

        results = run_training_pipeline(
            data_csv_path=data_csv_path,
            model_save_path=model_save_path,
            preprocessor_save_path=preprocessor_save_path,
            epochs=15,
            batch_size=64,
            lookback=24
        )

        # Deactivate any previous models
        ModelVersion.query.update({ModelVersion.is_active: False})

        # Save metadata record in DB
        version_tag = f"v1.0-lstm-{len(ModelVersion.query.all()) + 1}"
        m_version = ModelVersion(
            version_tag=version_tag,
            model_name="Stacked LSTM Disaster Hazard Forecasting Network",
            framework="TensorFlow 2.21 / Keras 3.15",
            architecture_summary={
                "layers": [
                    {"type": "Input", "shape": [24, 6]},
                    {"type": "LSTM", "units": 64, "return_sequences": True},
                    {"type": "Dropout", "rate": 0.2},
                    {"type": "LSTM", "units": 32, "return_sequences": False},
                    {"type": "Dropout", "rate": 0.2},
                    {"type": "Dense", "units": 16, "activation": "relu"},
                    {"type": "Dense", "units": 1, "activation": "sigmoid"}
                ],
                "optimizer": "Adam (lr=0.001)",
                "loss": "binary_crossentropy"
            },
            evaluation_metrics=results['lstm_metrics'],
            artifact_path=str(model_save_path),
            preprocessor_path=str(preprocessor_save_path),
            features_used=results['features'],
            lookback_steps=results['lookback_steps'],
            forecast_horizon_hours=24,
            is_active=True,
            training_dataset_period="180-Day Chronological Time Series"
        )
        db.session.add(m_version)
        db.session.commit()

        print("\n" + "=" * 70)
        print("TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"Active Model Version: {version_tag}")
        print(f"Untouched Test Accuracy:  {results['lstm_metrics']['accuracy'] * 100:.2f}%")
        print(f"Untouched Test Precision: {results['lstm_metrics']['precision'] * 100:.2f}%")
        print(f"Untouched Test Recall:    {results['lstm_metrics']['recall'] * 100:.2f}%")
        print(f"Untouched Test F1-Score:  {results['lstm_metrics']['f1_score']:.4f}")
        print(f"Untouched Test ROC-AUC:   {results['lstm_metrics']['roc_auc']:.4f}")
        print("-" * 70)
        print(f"Baseline Logistic Regression F1-Score: {results['baseline_metrics']['f1_score']:.4f}")
        print(f"Baseline Logistic Regression ROC-AUC:  {results['baseline_metrics']['roc_auc']:.4f}")
        print("=" * 70)

if __name__ == '__main__':
    main()
