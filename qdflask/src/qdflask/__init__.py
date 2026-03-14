"""
qdflask - QuickDev Flask Data Layer Package

Provides the SQLAlchemy database instance and User model for QuickDev
Flask applications. Authentication routes are provided by the separate
qdflaskauth package.

Usage:
    from qdflask import init_qdflask
    from qdflask.models import db, User

    app = Flask(__name__)
    init_qdflask(app, db_path='passwords.db')
"""

__version__ = '0.1.0'
__all__ = ['init_qdflask']


def init_qdflask(app, db_path='passwords.db'):
    """
    Initialize the data layer for a Flask application.

    Sets up SQLAlchemy and creates all tables.

    Args:
        app: Flask application instance
        db_path: Path to the database file.
                 Defaults to 'passwords.db'.
    """
    from qdflask.models import db

    app.config.setdefault(
        'SQLALCHEMY_DATABASE_URI', f'sqlite:///{db_path}')

    # Initialize database (skip if another extension already registered)
    if 'sqlalchemy' not in app.extensions:
        db.init_app(app)

    with app.app_context():
        db.create_all()
