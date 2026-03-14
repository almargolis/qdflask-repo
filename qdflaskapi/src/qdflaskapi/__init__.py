"""
qdflaskapi - QuickDev Flask API Key Authentication Package

Provides API key model, validation middleware, and key management routes.
Depends on qdflask for the data layer (db + User model).

Usage:
    from qdflaskapi import init_qdflaskapi

    init_qdflask(app)
    init_qdflaskauth(app)
    init_qdflaskapi(app, config={
        'enabled': True,
        'all_users_can_generate_api_keys': False,
        'is_api': False,
    })
"""

from flask import Blueprint

__version__ = '0.1.0'
__all__ = ['init_qdflaskapi', 'api_bp']

api_bp = Blueprint('api', __name__, url_prefix='/api')


def init_qdflaskapi(app, config=None):
    """
    Initialize API key authentication for a Flask application.

    Must be called AFTER init_qdflask() and init_qdflaskauth().

    Args:
        app: Flask application instance
        config: Dictionary of configuration options:
            - enabled: Enable API key system (default: False)
            - all_users_can_generate_api_keys: All users can create keys (default: False)
            - is_api: API-only app — validate keys on all routes (default: False)
    """
    config = config or {}

    enabled = config.get('enabled', False)
    all_users = config.get('all_users_can_generate_api_keys', False)
    is_api = config.get('is_api', False)

    # Always set config keys so other packages (qdflaskauth) can read them
    app.config['QDFLASKAPI_ENABLED'] = enabled
    app.config['QDFLASKAPI_ALL_USERS_CAN_GENERATE_API_KEYS'] = all_users
    app.config['QDFLASKAPI_IS_API'] = is_api

    if not enabled:
        app.logger.info(f"qdflaskapi initialized (v{__version__}) — DISABLED")
        return

    # Import models to register them with SQLAlchemy
    from qdflaskapi.models import APIKey, db

    # Create tables
    with app.app_context():
        db.create_all()

    # Register routes
    from qdflaskapi import routes  # noqa: F401
    app.register_blueprint(api_bp)

    # Register middleware
    from qdflaskapi.middleware import register_api_key_middleware
    register_api_key_middleware(app)

    # Context processor so templates can check api_enabled
    @app.context_processor
    def api_context():
        return {'api_enabled': True}

    app.logger.info(f"qdflaskapi initialized (v{__version__})")
    app.logger.info(f"  All users can generate keys: {all_users}")
    app.logger.info(f"  API-only mode: {is_api}")
