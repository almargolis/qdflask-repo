"""
Database models for qdflaskapi.

Provides APIKey model for API key authentication.

Note: This module imports the canonical db and User from qdflask.models to ensure
all Flask modules share the same database instance and User model.
"""

import secrets
from datetime import datetime
from qdflask.models import db, User


class APIKey(db.Model):
    """
    API key model for token-based authentication.

    Attributes:
        id: Primary key
        key: Unique API key string (64 chars, generated via secrets.token_urlsafe)
        user_id: Foreign key to users table
        purpose: Human-readable label for this key
        created_at: When key was created
        expires_at: When key expires (null = non-expiring)
        status: Key status ('a'=active, 'h'=hold)
        last_used_at: When key was last used for authentication
        created_by_ip: IP address that created the key
    """
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    purpose = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(1), nullable=False, default='a')  # 'a'=active, 'h'=hold
    last_used_at = db.Column(db.DateTime, nullable=True)
    created_by_ip = db.Column(db.String(45), nullable=True)

    user = db.relationship(User, backref='api_keys')

    def __repr__(self):
        return f'<APIKey {self.id} user={self.user_id} status={self.status}>'

    @property
    def is_valid(self):
        """Check if key is active and not expired."""
        if self.status != 'a':
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    @classmethod
    def generate(cls, user_id, purpose=None, expires_at=None, created_by_ip=None):
        """
        Create and persist a new API key.

        Args:
            user_id: ID of the user this key belongs to
            purpose: Human-readable label
            expires_at: Optional expiry datetime
            created_by_ip: IP address of requester

        Returns:
            New APIKey instance (already added to session and committed)
        """
        api_key = cls(
            key=secrets.token_urlsafe(32),
            user_id=user_id,
            purpose=purpose,
            expires_at=expires_at,
            created_by_ip=created_by_ip,
        )
        db.session.add(api_key)
        db.session.commit()
        return api_key

    @classmethod
    def validate(cls, key_string):
        """
        Look up a key and return the APIKey if it is valid.

        Args:
            key_string: The raw key string to validate

        Returns:
            APIKey instance if valid, None otherwise
        """
        api_key = cls.query.filter_by(key=key_string).first()
        if api_key and api_key.is_valid:
            return api_key
        return None
