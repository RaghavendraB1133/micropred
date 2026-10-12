from app.routes.health import health_bp
from app.routes.dashboard import dashboard_bp
from app.routes.zones import zones_bp
from app.routes.predictions import predictions_bp
from app.routes.datasets import datasets_bp
from app.routes.reports import reports_bp
from app.routes.alerts import alerts_bp

__all__ = [
    'health_bp',
    'dashboard_bp',
    'zones_bp',
    'predictions_bp',
    'datasets_bp',
    'reports_bp',
    'alerts_bp',
]
