"""
API key management routes for qdflaskapi.

Provides endpoints for creating, listing, and managing API keys.
"""

from datetime import datetime
from flask import request, jsonify
from flask_login import login_required, current_user

from qdflaskapi import api_bp
from qdflaskapi.models import APIKey, db


@api_bp.route('/keys', methods=['GET'])
@login_required
def list_keys():
    """List current user's API keys. Admins can pass ?user_id=N."""
    target_user_id = current_user.id

    requested_user_id = request.args.get('user_id', type=int)
    if requested_user_id is not None:
        if not current_user.is_admin():
            return jsonify(error="Admin access required"), 403
        target_user_id = requested_user_id

    keys = APIKey.query.filter_by(user_id=target_user_id).order_by(
        APIKey.created_at.desc()
    ).all()

    return jsonify(keys=[
        {
            'id': k.id,
            'key_prefix': k.key[:8] + '...',
            'purpose': k.purpose,
            'status': k.status,
            'created_at': k.created_at.isoformat() if k.created_at else None,
            'expires_at': k.expires_at.isoformat() if k.expires_at else None,
            'last_used_at': k.last_used_at.isoformat() if k.last_used_at else None,
        }
        for k in keys
    ])


@api_bp.route('/keys', methods=['POST'])
@login_required
def create_key():
    """Generate a new API key. Requires can_generate_api_keys permission."""
    if not current_user.can_generate_api_keys:
        return jsonify(error="You do not have permission to generate API keys"), 403

    data = request.get_json(silent=True) or {}
    purpose = data.get('purpose')

    expires_at = None
    if data.get('expires_at'):
        try:
            expires_at = datetime.fromisoformat(data['expires_at'])
        except (ValueError, TypeError):
            return jsonify(error="Invalid expires_at format (use ISO 8601)"), 400

    api_key = APIKey.generate(
        user_id=current_user.id,
        purpose=purpose,
        expires_at=expires_at,
        created_by_ip=request.remote_addr,
    )

    return jsonify(
        id=api_key.id,
        key=api_key.key,
        purpose=api_key.purpose,
        created_at=api_key.created_at.isoformat(),
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
    ), 201


@api_bp.route('/keys/<int:key_id>/hold', methods=['POST'])
@login_required
def hold_key(key_id):
    """Set an API key status to hold ('h'). Owner or admin only."""
    api_key = APIKey.query.get_or_404(key_id)
    if api_key.user_id != current_user.id and not current_user.is_admin():
        return jsonify(error="Not authorized"), 403

    api_key.status = 'h'
    db.session.commit()
    return jsonify(id=api_key.id, status=api_key.status)


@api_bp.route('/keys/<int:key_id>/activate', methods=['POST'])
@login_required
def activate_key(key_id):
    """Set an API key status to active ('a'). Owner or admin only."""
    api_key = APIKey.query.get_or_404(key_id)
    if api_key.user_id != current_user.id and not current_user.is_admin():
        return jsonify(error="Not authorized"), 403

    api_key.status = 'a'
    db.session.commit()
    return jsonify(id=api_key.id, status=api_key.status)


@api_bp.route('/keys/<int:key_id>', methods=['DELETE'])
@login_required
def delete_key(key_id):
    """Delete an API key. Owner or admin only."""
    api_key = APIKey.query.get_or_404(key_id)
    if api_key.user_id != current_user.id and not current_user.is_admin():
        return jsonify(error="Not authorized"), 403

    db.session.delete(api_key)
    db.session.commit()
    return jsonify(deleted=True)
