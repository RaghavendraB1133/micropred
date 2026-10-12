from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, Response
from sqlalchemy import func
from app.extensions import db
from app.models.zone import Zone
from app.models.prediction import Prediction
from app.models.model_version import ModelVersion
from app.services.data_service import DataService

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/summary', methods=['GET'])
def get_reports_summary():
    """
    Returns aggregated risk statistics, zone score averages, and active model metrics.
    """
    zone_stats = db.session.query(
        Zone.id,
        Zone.zone_code,
        Zone.name,
        func.count(Prediction.id).label('pred_count'),
        func.avg(Prediction.risk_score).label('avg_score'),
        func.max(Prediction.risk_score).label('max_score'),
    ).outerjoin(Prediction, Zone.id == Prediction.zone_id)\
     .group_by(Zone.id, Zone.zone_code, Zone.name).all()

    zone_breakdown = [
        {
            'zone_id': z.id,
            'zone_code': z.zone_code,
            'zone_name': z.name,
            'total_predictions': z.pred_count,
            'average_risk_score': round(float(z.avg_score or 0.0), 4),
            'max_risk_score': round(float(z.max_score or 0.0), 4)
        }
        for z in zone_stats
    ]

    active_model = ModelVersion.query.filter_by(is_active=True).first()

    return jsonify({
        'zone_statistics': zone_breakdown,
        'model_version': active_model.to_dict() if active_model else None,
        'report_generated_at': datetime.now(timezone.utc).isoformat()
    }), 200

@reports_bp.route('/reports/export', methods=['GET'])
def export_reports_csv():
    """
    Exports filtered prediction records as a downloadable CSV.
    """
    zone_id = request.args.get('zone_id')
    risk_category = request.args.get('risk_category')

    filters = {}
    if zone_id:
        filters['zone_id'] = zone_id
    if risk_category:
        filters['risk_category'] = risk_category

    csv_data = DataService.generate_predictions_csv(filters)

    filename = f"disaster_predictions_export.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
