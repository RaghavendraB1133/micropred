import os
from flask import Flask, jsonify
from app.config import config_by_name, Config
from app.extensions import db, migrate, cors
from app.utils.logger import logger

def create_app(config_name: str = None) -> Flask:
    """
    Application factory for the AI Disaster Prediction System.
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    config_obj = config_by_name.get(config_name, Config)
    app.config.from_object(config_obj)

    # Ensure required runtime directories exist
    app.config['ARTIFACTS_DIR'].mkdir(parents=True, exist_ok=True)
    app.config['MODELS_DIR'].mkdir(parents=True, exist_ok=True)
    app.config['PREPROCESSING_DIR'].mkdir(parents=True, exist_ok=True)
    app.config['DATA_DIR'].mkdir(parents=True, exist_ok=True)
    app.config['RAW_DATA_DIR'].mkdir(parents=True, exist_ok=True)
    app.config['PROCESSED_DATA_DIR'].mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config['CORS_ALLOWED_ORIGINS']}},
        supports_credentials=True
    )

    # Register blueprints with /api/v1 prefix
    from app.routes import (
        health_bp,
        dashboard_bp,
        zones_bp,
        predictions_bp,
        datasets_bp,
        reports_bp,
        alerts_bp
    )

    app.register_blueprint(health_bp, url_prefix='/api/v1')
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1')
    app.register_blueprint(zones_bp, url_prefix='/api/v1')
    app.register_blueprint(predictions_bp, url_prefix='/api/v1')
    app.register_blueprint(datasets_bp, url_prefix='/api/v1')
    app.register_blueprint(reports_bp, url_prefix='/api/v1')
    app.register_blueprint(alerts_bp, url_prefix='/api/v1')

    # Global error handlers for consistent JSON API responses
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request', 'message': str(error.description if hasattr(error, 'description') else error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found', 'message': 'The requested resource was not found on this server.'}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': 'Method Not Allowed', 'message': 'HTTP method not allowed for this endpoint.'}), 405

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected server error occurred.'}), 500

    logger.info(f"Flask Application initialized with config '{config_name}'")
    return app
