"""
Tests for qdflaskapi package.
"""

import pytest
from datetime import datetime, timedelta
from flask import Flask, g
from flask_login import login_required, current_user
from qdflask import init_qdflask
from qdflask.models import User, db
from qdflaskauth import init_qdflaskauth
from qdflaskapi import init_qdflaskapi
from qdflaskapi.models import APIKey


# --- Fixtures ---

@pytest.fixture
def app():
    """Create a test app with qdflaskapi enabled."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False

    init_qdflask(app)
    init_qdflaskauth(app, roles=['admin', 'editor'])
    init_qdflaskapi(app, config={
        'enabled': True,
        'all_users_can_generate_api_keys': False,
        'is_api': False,
    })

    @app.route('/')
    def index():
        return "Home"

    # A non-API route for middleware testing
    @app.route('/normal')
    def normal_page():
        return "Normal page"

    with app.app_context():
        yield app
        db.drop_all()


@pytest.fixture
def api_only_app():
    """Create a test app with is_api=True (API-only mode)."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False

    init_qdflask(app)
    init_qdflaskauth(app, roles=['admin', 'editor'])
    init_qdflaskapi(app, config={
        'enabled': True,
        'all_users_can_generate_api_keys': False,
        'is_api': True,
    })

    @app.route('/')
    def index():
        return "Home"

    @app.route('/normal')
    def normal_page():
        return "Normal page"

    with app.app_context():
        yield app
        db.drop_all()


@pytest.fixture
def disabled_app():
    """Create a test app with qdflaskapi disabled."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False

    init_qdflask(app)
    init_qdflaskauth(app, roles=['admin', 'editor'])
    init_qdflaskapi(app, config={'enabled': False})

    with app.app_context():
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def api_only_client(api_only_app):
    return api_only_app.test_client()


@pytest.fixture
def user_with_keys(app):
    """Create a user with can_generate_api_keys=True."""
    user = User(username='apiuser', role='editor', can_generate_api_keys=True)
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def user_without_keys(app):
    """Create a user without API key permission."""
    user = User(username='nokeys', role='editor', can_generate_api_keys=False)
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


def _login(client, username, password):
    """Log in via the auth blueprint."""
    client.post('/auth/login', data={
        'username': username,
        'password': password,
    })


# --- Model tests ---

class TestAPIKeyModel:

    def test_generate_creates_key(self, app, user_with_keys):
        api_key = APIKey.generate(user_id=user_with_keys.id, purpose='testing')
        assert api_key.id is not None
        assert len(api_key.key) > 0
        assert api_key.user_id == user_with_keys.id
        assert api_key.purpose == 'testing'
        assert api_key.status == 'a'

    def test_validate_finds_valid_key(self, app, user_with_keys):
        api_key = APIKey.generate(user_id=user_with_keys.id, purpose='test')
        result = APIKey.validate(api_key.key)
        assert result is not None
        assert result.id == api_key.id

    def test_validate_returns_none_for_expired_key(self, app, user_with_keys):
        api_key = APIKey.generate(
            user_id=user_with_keys.id,
            purpose='expired',
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        result = APIKey.validate(api_key.key)
        assert result is None

    def test_validate_returns_none_for_held_key(self, app, user_with_keys):
        api_key = APIKey.generate(user_id=user_with_keys.id, purpose='held')
        api_key.status = 'h'
        db.session.commit()
        result = APIKey.validate(api_key.key)
        assert result is None

    def test_validate_returns_none_for_unknown_key(self, app):
        result = APIKey.validate('nonexistent-key-value')
        assert result is None

    def test_is_valid_property(self, app, user_with_keys):
        api_key = APIKey.generate(user_id=user_with_keys.id, purpose='test')
        assert api_key.is_valid is True

        api_key.status = 'h'
        assert api_key.is_valid is False

        api_key.status = 'a'
        api_key.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert api_key.is_valid is False

    def test_generate_sets_created_by_ip(self, app, user_with_keys):
        api_key = APIKey.generate(
            user_id=user_with_keys.id,
            purpose='ip test',
            created_by_ip='192.168.1.1',
        )
        assert api_key.created_by_ip == '192.168.1.1'

    def test_user_relationship(self, app, user_with_keys):
        api_key = APIKey.generate(user_id=user_with_keys.id, purpose='rel test')
        assert api_key.user.username == 'apiuser'

    def test_user_backref(self, app, user_with_keys):
        APIKey.generate(user_id=user_with_keys.id, purpose='key1')
        APIKey.generate(user_id=user_with_keys.id, purpose='key2')
        assert len(user_with_keys.api_keys) == 2


# --- Middleware tests ---

class TestMiddleware:

    def test_valid_bearer_sets_g_user(self, app, client, user_with_keys):
        api_key = APIKey.generate(user_id=user_with_keys.id, purpose='mw test')

        with app.test_request_context():
            response = client.get('/api/keys',
                headers={'Authorization': f'Bearer {api_key.key}'},
            )
            # Even though we're not logged in via session, the middleware
            # sets g.current_api_user. The route still requires @login_required
            # so this returns 401/302 — but the key itself is validated.
            # We test the full flow via route tests below.

        # Verify last_used_at was updated
        db.session.refresh(api_key)
        assert api_key.last_used_at is not None

    def test_missing_header_returns_401_on_api_route(self, client):
        response = client.get('/api/keys')
        # No Authorization header on an API route:
        # The @login_required decorator fires first and redirects/returns 401
        assert response.status_code in (401, 302)

    def test_invalid_key_returns_401(self, client):
        response = client.get('/api/keys',
            headers={'Authorization': 'Bearer invalid-key-here'},
        )
        assert response.status_code == 401

    def test_non_api_route_unaffected_when_not_api_mode(self, client):
        response = client.get('/normal')
        assert response.status_code == 200
        assert b'Normal page' in response.data

    def test_api_only_mode_validates_all_routes(self, api_only_client):
        # In API-only mode, non-API routes also require Bearer token
        response = api_only_client.get('/normal')
        assert response.status_code == 401

    def test_api_only_mode_valid_key_passes(self, api_only_app, api_only_client):
        user = User(username='apiuser2', role='editor', can_generate_api_keys=True)
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()

        api_key = APIKey.generate(user_id=user.id, purpose='api-only test')

        response = api_only_client.get('/normal',
            headers={'Authorization': f'Bearer {api_key.key}'},
        )
        assert response.status_code == 200


# --- Route tests ---

class TestRoutes:

    def test_create_key_with_permission(self, app, client, user_with_keys):
        _login(client, 'apiuser', 'password123')
        response = client.post('/api/keys',
            json={'purpose': 'my new key'},
            content_type='application/json',
        )
        assert response.status_code == 201
        data = response.get_json()
        assert 'key' in data
        assert data['purpose'] == 'my new key'
        assert len(data['key']) > 0

    def test_create_key_without_permission_returns_403(self, app, client, user_without_keys):
        _login(client, 'nokeys', 'password123')
        response = client.post('/api/keys',
            json={'purpose': 'should fail'},
            content_type='application/json',
        )
        assert response.status_code == 403

    def test_list_keys(self, app, client, user_with_keys):
        APIKey.generate(user_id=user_with_keys.id, purpose='key1')
        APIKey.generate(user_id=user_with_keys.id, purpose='key2')

        _login(client, 'apiuser', 'password123')
        response = client.get('/api/keys')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['keys']) == 2
        # Keys should be masked (prefix only)
        assert data['keys'][0]['key_prefix'].endswith('...')

    def test_list_keys_admin_sees_other_user(self, app, client, user_with_keys):
        APIKey.generate(user_id=user_with_keys.id, purpose='their key')

        _login(client, 'admin', 'admin')
        response = client.get(f'/api/keys?user_id={user_with_keys.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['keys']) == 1

    def test_list_keys_non_admin_cannot_see_others(self, app, client, user_with_keys):
        _login(client, 'apiuser', 'password123')
        # Try to see admin's keys
        admin = User.get_by_username('admin')
        response = client.get(f'/api/keys?user_id={admin.id}')
        assert response.status_code == 403

    def test_hold_key(self, app, client, user_with_keys):
        api_key = APIKey.generate(user_id=user_with_keys.id, purpose='to hold')
        _login(client, 'apiuser', 'password123')

        response = client.post(f'/api/keys/{api_key.id}/hold')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'h'

        db.session.refresh(api_key)
        assert api_key.status == 'h'

    def test_activate_key(self, app, client, user_with_keys):
        api_key = APIKey.generate(user_id=user_with_keys.id, purpose='to activate')
        api_key.status = 'h'
        db.session.commit()

        _login(client, 'apiuser', 'password123')
        response = client.post(f'/api/keys/{api_key.id}/activate')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'a'

    def test_delete_key(self, app, client, user_with_keys):
        api_key = APIKey.generate(user_id=user_with_keys.id, purpose='to delete')
        key_id = api_key.id

        _login(client, 'apiuser', 'password123')
        response = client.delete(f'/api/keys/{key_id}')
        assert response.status_code == 200

        assert APIKey.query.get(key_id) is None

    def test_hold_key_admin_can_act_on_others(self, app, client, user_with_keys):
        api_key = APIKey.generate(user_id=user_with_keys.id, purpose='admin hold')
        _login(client, 'admin', 'admin')

        response = client.post(f'/api/keys/{api_key.id}/hold')
        assert response.status_code == 200

    def test_non_owner_non_admin_cannot_modify(self, app, client, user_with_keys, user_without_keys):
        api_key = APIKey.generate(user_id=user_with_keys.id, purpose='protected')
        _login(client, 'nokeys', 'password123')

        response = client.post(f'/api/keys/{api_key.id}/hold')
        assert response.status_code == 403

    def test_create_key_with_expires_at(self, app, client, user_with_keys):
        _login(client, 'apiuser', 'password123')
        future = (datetime.utcnow() + timedelta(days=30)).isoformat()
        response = client.post('/api/keys',
            json={'purpose': 'expiring key', 'expires_at': future},
            content_type='application/json',
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['expires_at'] is not None

    def test_create_key_invalid_expires_at(self, app, client, user_with_keys):
        _login(client, 'apiuser', 'password123')
        response = client.post('/api/keys',
            json={'purpose': 'bad date', 'expires_at': 'not-a-date'},
            content_type='application/json',
        )
        assert response.status_code == 400


# --- Config tests ---

class TestConfig:

    def test_disabled_mode_skips_blueprint(self, disabled_app):
        assert 'api' not in disabled_app.blueprints

    def test_disabled_mode_sets_config_keys(self, disabled_app):
        assert disabled_app.config['QDFLASKAPI_ENABLED'] is False
        assert disabled_app.config['QDFLASKAPI_ALL_USERS_CAN_GENERATE_API_KEYS'] is False

    def test_enabled_mode_registers_blueprint(self, app):
        assert 'api' in app.blueprints

    def test_enabled_mode_sets_config_keys(self, app):
        assert app.config['QDFLASKAPI_ENABLED'] is True
        assert app.config['QDFLASKAPI_IS_API'] is False
