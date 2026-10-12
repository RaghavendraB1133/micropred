from datetime import datetime, timezone
from app.extensions import db

class DatasetMetadata(db.Model):
    __tablename__ = 'dataset_metadata'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=False)
    row_count = db.Column(db.Integer, nullable=False, default=0)
    columns_detected = db.Column(db.JSON, nullable=False)
    date_range_start = db.Column(db.DateTime, nullable=True)
    date_range_end = db.Column(db.DateTime, nullable=True)
    validation_status = db.Column(db.String(32), default='VALIDATED', nullable=False)  # 'VALIDATED', 'FAILED', 'PENDING'
    data_quality_report = db.Column(db.JSON, nullable=True)  # missing values %, duplicate count, coordinate checks
    dataset_type = db.Column(db.String(64), default='Historical Weather & Hazard')
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_size_bytes': self.file_size_bytes,
            'row_count': self.row_count,
            'columns_detected': self.columns_detected,
            'date_range_start': self.date_range_start.isoformat() if self.date_range_start else None,
            'date_range_end': self.date_range_end.isoformat() if self.date_range_end else None,
            'validation_status': self.validation_status,
            'data_quality_report': self.data_quality_report,
            'dataset_type': self.dataset_type,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
