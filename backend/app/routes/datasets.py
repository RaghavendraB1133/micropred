import os
import pandas as pd
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.dataset import DatasetMetadata
from app.models.zone import Zone
from app.models.weather import WeatherObservation
from app.ml.dataset_loader import validate_and_assess_dataset
from app.utils.logger import logger

datasets_bp = Blueprint('datasets', __name__)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@datasets_bp.route('/datasets/status', methods=['GET'])
def get_dataset_status():
    """
    Returns registered dataset provenance, validation statuses, and row counts.
    """
    datasets = DatasetMetadata.query.order_by(DatasetMetadata.created_at.desc()).all()
    total_observations = WeatherObservation.query.count()

    return jsonify({
        'datasets': [d.to_dict() for d in datasets],
        'total_observations': total_observations,
        'storage_info': {
            'raw_dir': str(current_app.config['RAW_DATA_DIR']),
            'processed_dir': str(current_app.config['PROCESSED_DATA_DIR'])
        }
    }), 200

@datasets_bp.route('/datasets/validate', methods=['POST'])
def validate_dataset():
    """
    Validates an uploaded CSV dataset for required fields, coordinates, and null percentages.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded in form field "file"'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only CSV files (.csv) are supported'}), 400

    try:
        df = pd.read_csv(file)
    except Exception as e:
        return jsonify({'error': f'Failed to parse CSV file: {str(e)}'}), 400

    report = validate_and_assess_dataset(df)
    return jsonify({
        'filename': secure_filename(file.filename),
        'validation_report': report
    }), 200

@datasets_bp.route('/datasets/import', methods=['POST'])
def import_dataset():
    """
    Imports and commits validated CSV data into database.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded in form field "file"'}), 400

    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only CSV files (.csv) are supported'}), 400

    filename = secure_filename(file.filename)
    save_path = current_app.config['RAW_DATA_DIR'] / filename
    file.save(str(save_path))

    try:
        df = pd.read_csv(save_path)
    except Exception as e:
        return jsonify({'error': f'Failed to parse CSV file: {str(e)}'}), 400

    report = validate_and_assess_dataset(df)
    if not report['is_valid']:
        return jsonify({
            'error': 'Dataset failed validation requirements.',
            'validation_report': report
        }), 422

    # Save metadata record
    meta = DatasetMetadata(
        filename=filename,
        file_size_bytes=save_path.stat().st_size,
        row_count=len(df),
        columns_detected=list(df.columns),
        date_range_start=pd.to_datetime(df['timestamp']).min() if 'timestamp' in df.columns else None,
        date_range_end=pd.to_datetime(df['timestamp']).max() if 'timestamp' in df.columns else None,
        validation_status='VALIDATED',
        data_quality_report=report,
        description=f'Imported dataset containing {len(df)} records.'
    )
    db.session.add(meta)
    db.session.commit()

    return jsonify({
        'message': f'Dataset {filename} successfully validated and registered.',
        'dataset_id': meta.id,
        'summary': {
            'total_rows': len(df),
            'validation_report': report
        }
    }), 201
