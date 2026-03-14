"""
qdflaskemail - QuickDev Flask Email Package

A standalone email service package that wraps qdemail and provides
admin notification helpers. Can be disabled via config to silently no-op.

Usage:
    from qdflaskemail import init_qdflaskemail, send_email, send_to_admins

    init_qdflaskemail(app)

    send_to_admins("Alert", "Something happened.")
"""

__version__ = '0.1.0'
__all__ = [
    'init_qdflaskemail',
    'send_email',
    'send_to_admins',
    'get_verified_admin_emails',
]

from qdflaskemail.email import send_email, send_to_admins, get_verified_admin_emails


def init_qdflaskemail(app, config=None):
    """
    Initialize qdflaskemail for a Flask application.

    Sets the QDFLASKEMAIL_ENABLED config default. When disabled,
    all email functions silently no-op.

    Args:
        app: Flask application instance
        config: Optional dict with configuration overrides
    """
    if config is None:
        config = {}

    app.config.setdefault(
        'QDFLASKEMAIL_ENABLED',
        config.get('enabled', True)
    )
