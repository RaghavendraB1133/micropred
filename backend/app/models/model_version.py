from datetime import datetime, timezone
from app.extensions import db

class ModelVersion(db.Model):
    __tablename__ = 'model_versions'

    id = db.Column(db.Integer, primary_key=True)
    version_tag = db.Column(db.String(64), unique=True, nullable=False, index=True)
    model_name = db.Column(db.String(128), nullable=False)
    framework = db.Column(db.String(64), default='TensorFlow / Keras LSTM')
    architecture_summary = db.Column(db.JSON, nullable=True)
    evaluation_metrics = db.Column(db.JSON, nullable=True)  # { "accuracy": 0.88, "precision": 0.84, "recall": 0.86, "f1": 0.85, "auc": 0.91 }
    artifact_path = db.Column(db.String(256), nullable=False)
    preprocessor_path = db.Column(db.String(256), nullable=False)
    features_used = db.Column(db.JSON, nullable=True)
    lookback_steps = db.Column(db.Integer, default=24)
    forecast_horizon_hours = db.Column(db.Integer, default=24)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    training_dataset_period = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    predictions = db.relationship('Prediction', backref='model_version', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'version_tag': self.version_tag,
            'model_name': self.model_name,
            'framework': self.framework,
            'architecture_summary': self.architecture_summary,
            'evaluation_metrics': self.evaluation_metrics,
            'artifact_path': self.artifact_path,
            'preprocessor_path': self.preprocessor_path,
            'features_used': self.features_used,
            'lookback_steps': self.lookback_steps,
            'forecast_horizon_hours': self.forecast_horizon_hours,
            'is_active': self.is_active,
            'training_dataset_period': self.training_dataset_period,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
