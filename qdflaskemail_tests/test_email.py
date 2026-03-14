"""
Tests for qdflaskemail package.
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from qdflask import init_qdflask
from qdflask.models import User, db
from qdflaskemail import init_qdflaskemail, send_email, send_to_admins, get_verified_admin_emails


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'

    init_qdflask(app)
    init_qdflaskemail(app)

    with app.app_context():
        yield app
        db.drop_all()


def _create_admin(username, email, verified='Y'):
    """Helper to create an admin user with email settings."""
    user = User(username=username, role='admin',
                email_address=email, email_verified=verified)
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    return user


@patch('qdflaskemail.email._qdemail_send')
def test_send_to_admins_with_verified_admins(mock_send, app):
    """Test send_to_admins sends to verified admin users."""
    with app.app_context():
        _create_admin('admin1', 'admin1@example.com', verified='Y')
        _create_admin('admin2', 'admin2@example.com', verified='Y')

        mock_send.return_value = True
        result = send_to_admins("Test Subject", "Test body")

        assert result is True
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == "Test Subject"
        assert set(call_args[0][1]) == {'admin1@example.com', 'admin2@example.com'}
        assert call_args[0][2] == "Test body"


@patch('qdflaskemail.email._qdemail_send')
def test_send_to_admins_no_verified_admins(mock_send, app):
    """Test send_to_admins returns False when no verified admins exist."""
    with app.app_context():
        _create_admin('admin1', 'admin1@example.com', verified='N')

        result = send_to_admins("Test Subject", "Test body")

        assert result is False
        mock_send.assert_not_called()


@patch('qdflaskemail.email._qdemail_send')
def test_send_email_delegates_to_qdemail(mock_send, app):
    """Test send_email delegates to qdemail.send_email when enabled."""
    with app.app_context():
        mock_send.return_value = True
        result = send_email("Subject", ["user@example.com"], "Body")

        assert result is True
        mock_send.assert_called_once_with(
            "Subject", ["user@example.com"], "Body", sender=None
        )


@patch('qdflaskemail.email._qdemail_send')
def test_send_email_disabled_noop(mock_send, app):
    """Test send_email returns False when disabled, without calling qdemail."""
    with app.app_context():
        app.config['QDFLASKEMAIL_ENABLED'] = False

        result = send_email("Subject", ["user@example.com"], "Body")

        assert result is False
        mock_send.assert_not_called()


@patch('qdflaskemail.email._qdemail_send')
def test_send_to_admins_disabled_noop(mock_send, app):
    """Test send_to_admins returns False when disabled, without calling qdemail."""
    with app.app_context():
        app.config['QDFLASKEMAIL_ENABLED'] = False
        _create_admin('admin1', 'admin1@example.com', verified='Y')

        result = send_to_admins("Test Subject", "Test body")

        assert result is False
        mock_send.assert_not_called()


def test_get_verified_admin_emails_returns_list(app):
    """Test get_verified_admin_emails returns correct email list."""
    with app.app_context():
        _create_admin('admin1', 'admin1@example.com', verified='Y')
        _create_admin('admin2', 'admin2@example.com', verified='Y')
        _create_admin('admin3', 'admin3@example.com', verified='N')
        _create_admin('admin4', '', verified='Y')  # blank email

        emails = get_verified_admin_emails()

        assert set(emails) == {'admin1@example.com', 'admin2@example.com'}


def test_get_verified_admin_emails_disabled(app):
    """Test get_verified_admin_emails returns empty list when disabled."""
    with app.app_context():
        app.config['QDFLASKEMAIL_ENABLED'] = False
        _create_admin('admin1', 'admin1@example.com', verified='Y')

        emails = get_verified_admin_emails()

        assert emails == []


def test_init_qdflaskemail_sets_default(app):
    """Test init_qdflaskemail sets QDFLASKEMAIL_ENABLED default."""
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True

    init_qdflaskemail(test_app)
    assert test_app.config['QDFLASKEMAIL_ENABLED'] is True


def test_init_qdflaskemail_config_override():
    """Test init_qdflaskemail respects config override."""
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True

    init_qdflaskemail(test_app, config={'enabled': False})
    assert test_app.config['QDFLASKEMAIL_ENABLED'] is False


def test_init_qdflaskemail_does_not_override_existing():
    """Test init_qdflaskemail does not override existing config value."""
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    test_app.config['QDFLASKEMAIL_ENABLED'] = False

    init_qdflaskemail(test_app)  # default would be True
    assert test_app.config['QDFLASKEMAIL_ENABLED'] is False
