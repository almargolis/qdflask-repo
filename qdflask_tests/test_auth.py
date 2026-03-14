"""
Tests for qdflask data layer.
"""

import pytest
from flask import Flask
from qdflask import init_qdflask
from qdflask.models import User, db


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'

    init_qdflask(app)

    with app.app_context():
        yield app
        db.drop_all()


def test_init_qdflask(app):
    """Test that data layer initialization works."""
    assert 'sqlalchemy' in app.extensions


def test_user_password_hashing(app):
    """Test password hashing and verification."""
    with app.app_context():
        user = User(username='testuser', role='viewer')
        user.set_password('secret123')
        db.session.add(user)
        db.session.commit()

        assert user.check_password('secret123')
        assert not user.check_password('wrongpassword')


def test_user_roles(app):
    """Test user role checking."""
    with app.app_context():
        admin = User(username='admin', role='admin')
        editor = User(username='editor', role='editor')

        assert admin.is_admin()
        assert not editor.is_admin()

        assert admin.has_role('admin')
        assert editor.has_role('editor')
        assert not editor.has_role('admin')


def test_user_creation(app):
    """Test creating and retrieving a user."""
    with app.app_context():
        user = User(username='newuser', role='editor')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        retrieved = User.get_by_username('newuser')
        assert retrieved is not None
        assert retrieved.role == 'editor'
        assert retrieved.is_active is True
