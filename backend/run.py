import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from app.extensions import db
from app.services.data_service import DataService
from app.utils.logger import logger

app = create_app(os.getenv('FLASK_ENV', 'development'))

def init_db():
    with app.app_context():
        db.create_all()
        # Seed initial micro-zones and historical observations if empty
        DataService.seed_initial_data_if_empty()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')

    init_db()

    is_production = os.getenv('FLASK_ENV') == 'production'

    if is_production:
        try:
            from waitress import serve
            logger.info(f"Serving production application with Waitress on http://{host}:{port}")
            serve(app, host=host, port=port, threads=8)
        except ImportError:
            logger.warning("Waitress not found, falling back to standard server.")
            app.run(host=host, port=port, debug=False)
    else:
        logger.info(f"Starting Flask development server on http://127.0.0.1:{port}")
        app.run(host=host, port=port, debug=True)
