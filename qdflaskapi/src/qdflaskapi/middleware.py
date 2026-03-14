"""
API key validation middleware for qdflaskapi.

Registers a before_request handler that extracts and validates API keys
from the Authorization header.
"""

from datetime import datetime
from flask import request, g, jsonify
from flask_login import current_user


def register_api_key_middleware(app):
    """
    Register a before_request handler for API key validation.

    Behavior depends on QDFLASKAPI_IS_API config:
    - True: validate on ALL routes (API-only app)
    - False: validate only on routes under the 'api' blueprint

    Users already authenticated via session (Flask-Login) are allowed through
    without a Bearer token — this lets the key management routes work with
    both session and API key authentication.
    """
    @app.before_request
    def validate_api_key():
        from qdflaskapi.models import APIKey, db

        is_api_app = app.config.get('QDFLASKAPI_IS_API', False)
        on_api_blueprint = request.blueprints and 'api' in request.blueprints

        # Determine if this request needs API key validation
        if not is_api_app and not on_api_blueprint:
            return None

        # If user is already logged in via session, skip API key check
        if current_user.is_authenticated:
            return None

        # Extract Bearer token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            if is_api_app or on_api_blueprint:
                return jsonify(error="Missing or invalid Authorization header"), 401
            return None

        token = auth_header[7:]  # Strip 'Bearer '
        api_key = APIKey.validate(token)

        if api_key is None:
            return jsonify(error="Invalid or expired API key"), 401

        # Valid key — set user on g and update last_used_at
        g.current_api_user = api_key.user
        api_key.last_used_at = datetime.utcnow()
        db.session.commit()

        return None
