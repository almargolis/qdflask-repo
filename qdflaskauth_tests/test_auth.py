"""
Tests for qdflaskauth authentication package.
"""

import pytest
from flask import Flask
from qdflask import init_qdflask
from qdflask.models import User, db
from qdflaskauth import init_qdflaskauth, create_admin_user, require_role


@pytest.fixture
def app():
    """Create and configure a test Flask application with auth enabled."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False

    init_qdflask(app)
    init_qdflaskauth(app, roles=['admin', 'editor', 'viewer'])

    @app.route('/')
    def index():
        return "Home"

    with app.app_context():
        yield app
        db.drop_all()


@pytest.fixture
def disabled_app():
    """Create a test Flask application with auth disabled (read-only mode)."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'

    init_qdflask(app)
    init_qdflaskauth(app, enabled=False)

    @app.route('/')
    def index():
        return "Home"

    from flask_login import login_required

    @app.route('/protected')
    @login_required
    def protected():
        return "Secret"

    with app.app_context():
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def disabled_client(disabled_app):
    """Create a test client for disabled app."""
    return disabled_app.test_client()


def test_init_registers_blueprint(app):
    """Test that init_qdflaskauth registers the auth blueprint."""
    assert 'auth' in app.blueprints


def test_init_sets_roles(app):
    """Test that init_qdflaskauth sets QDFLASK_ROLES in config."""
    assert app.config['QDFLASK_ROLES'] == ['admin', 'editor', 'viewer']


def test_init_sets_enabled_flag(app):
    """Test that init_qdflaskauth sets QDFLASKAUTH_ENABLED."""
    assert app.config['QDFLASKAUTH_ENABLED'] is True


def test_create_admin_user(app):
    """Test creating an admin user."""
    with app.app_context():
        create_admin_user('testadmin', 'password123')
        user = User.get_by_username('testadmin')
        assert user is not None
        assert user.username == 'testadmin'
        assert user.role == 'admin'
        assert user.check_password('password123')


def test_create_admin_user_updates_existing(app):
    """Test that create_admin_user updates an existing user."""
    with app.app_context():
        create_admin_user('testadmin', 'oldpassword')
        create_admin_user('testadmin', 'newpassword')
        user = User.get_by_username('testadmin')
        assert user.check_password('newpassword')
        assert not user.check_password('oldpassword')


def test_login_route_renders(client):
    """Test that login route renders the login form."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_login_with_valid_credentials(app, client):
    """Test login with valid credentials."""
    with app.app_context():
        create_admin_user('testuser', 'secret123')

    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'secret123'
    }, follow_redirects=False)
    assert response.status_code == 302


def test_login_with_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post('/auth/login', data={
        'username': 'nonexistent',
        'password': 'wrong'
    })
    assert response.status_code == 401


def test_disabled_mode_sets_flag(disabled_app):
    """Test that disabled mode sets QDFLASKAUTH_ENABLED to False."""
    assert disabled_app.config['QDFLASKAUTH_ENABLED'] is False


def test_disabled_mode_no_auth_routes(disabled_app):
    """Test that disabled mode does not register auth blueprint."""
    assert 'auth' not in disabled_app.blueprints


def test_disabled_mode_returns_403(disabled_client):
    """Test that disabled mode returns 403 for protected routes."""
    response = disabled_client.get('/protected')
    assert response.status_code == 403
    assert b'Authentication is disabled' in response.data


def test_disabled_mode_no_admin_seeded(disabled_app):
    """Test that no admin user is seeded when disabled."""
    with disabled_app.app_context():
        assert User.query.count() == 0


def test_disabled_mode_auth_routes_404(disabled_client):
    """Test that auth routes return 404 when disabled."""
    response = disabled_client.get('/auth/login')
    assert response.status_code == 404


def test_roles_must_include_admin():
    """Test that init_qdflaskauth raises ValueError if roles don't include admin."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'

    init_qdflask(app)
    with pytest.raises(ValueError, match="roles must include 'admin'"):
        init_qdflaskauth(app, roles=['editor', 'viewer'])


def test_admin_seeded_when_no_users(app):
    """Test that admin user is auto-seeded when database has no users."""
    with app.app_context():
        # init_qdflaskauth already ran in fixture, so admin should exist
        admin = User.get_by_username('admin')
        assert admin is not None
        assert admin.role == 'admin'
