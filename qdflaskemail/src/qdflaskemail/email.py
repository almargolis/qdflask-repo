"""qdflaskemail.email — Email helpers that depend on the User model."""
import logging
from flask import current_app
from qdemail import send_email as _qdemail_send  # noqa: F401


def _is_enabled():
    """Check if qdflaskemail is enabled via app config."""
    return current_app.config.get('QDFLASKEMAIL_ENABLED', True)


def send_email(subject, recipients, body, sender=None):
    """
    Send an email via qdemail.

    When QDFLASKEMAIL_ENABLED is False, returns False without sending.

    Args:
        subject: Email subject line
        recipients: List of recipient email addresses
        body: Plain text email body
        sender: Optional sender email

    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not _is_enabled():
        return False

    return _qdemail_send(subject, recipients, body, sender=sender)


def get_verified_admin_emails():
    """
    Get list of verified admin email addresses.

    When QDFLASKEMAIL_ENABLED is False, returns empty list.

    Returns:
        List of email addresses for admins with email_verified='Y'
    """
    if not _is_enabled():
        return []

    from qdflask.models import User
    admin_users = User.get_verified_admins()
    return [u.email_address for u in admin_users if u.email_address]


def send_to_admins(subject, body, sender=None):
    """
    Send email to all verified admins.

    When QDFLASKEMAIL_ENABLED is False, returns False without sending.

    Args:
        subject: Email subject line
        body: Plain text email body
        sender: Optional sender email

    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not _is_enabled():
        return False

    recipients = get_verified_admin_emails()

    if not recipients:
        logging.info("No verified admin emails - skipping notification")
        return False

    return _qdemail_send(subject, recipients, body, sender=sender)
