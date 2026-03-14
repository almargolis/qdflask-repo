"""
qdflaskauth - QuickDev Flask Authentication Package

Provides Flask-Login integration, role-based access control, user management
routes, and CLI tools. Depends on qdflask for the data layer (db + User model).

Usage:
    from qdflaskauth import init_qdflaskauth, create_admin_user, require_role

    app = Flask(__name__)

    # Initialize data layer first
    init_qdflask(app)

    # Initialize authentication
    init_qdflaskauth(app, roles=['admin', 'editor', 'viewer'])
"""

from flask_login import LoginManager
from flask import jsonify

__version__ = '0.1.0'
__all__ = ['init_qdflaskauth', 'create_admin_user', 'require_role',
           'login_manager']

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    from qdflask.models import User
    return User.get(user_id)


def init_qdflaskauth(app, enabled=True, roles=None,
                     login_view='auth.login'):
    """
    Initialize authentication for a Flask application.

    Args:
        app: Flask application instance
        enabled: Whether auth routes are enabled. When False, login_manager
                 is still initialized but auth routes are not registered
                 and unauthorized requests return 403 JSON.
        roles: List of valid role names. Must include 'admin'.
               Defaults to ['admin', 'editor']
        login_view: The view to redirect to when login is required
    """
    app.config['QDFLASKAUTH_ENABLED'] = enabled

    if roles is None:
        roles = ['admin', 'editor']

    if 'admin' not in roles:
        raise ValueError("roles must include 'admin'")

    app.config['QDFLASK_ROLES'] = roles

    # Always initialize login manager
    login_manager.init_app(app)

    if enabled:
        # Full auth mode
        login_manager.login_view = login_view

        # Register auth blueprint
        from qdflaskauth.auth import auth_bp
        app.register_blueprint(auth_bp)

        # Seed admin user if no users exist
        with app.app_context():
            from qdflask.models import User
            if User.query.count() == 0:
                create_admin_user()
                app.logger.info(
                    "Created initial admin user (admin/admin)"
                    " - change password after first login"
                )
    else:
        # Read-only mode: no routes, 403 on unauthorized
        @login_manager.unauthorized_handler
        def unauthorized():
            return jsonify(error="Authentication is disabled"), 403


def create_admin_user(username='admin', password='admin'):
    """
    Create or update the admin user.

    Must be called within app context.

    Args:
        username: Username for admin user
        password: Password for admin user

    Returns:
        User object
    """
    from qdflask.models import db, User

    admin = User.get_by_username(username)

    if admin:
        # Update existing admin
        admin.role = 'admin'
        admin.set_password(password)
        admin.is_active = True
    else:
        # Create new admin
        admin = User(username=username, role='admin')
        admin.set_password(password)
        db.session.add(admin)

    db.session.commit()
    return admin


def require_role(*roles):
    """
    Decorator to require specific roles for a route.

    Args:
        *roles: One or more role names required to access the route

    Example:
        @app.route('/admin')
        @login_required
        @require_role('admin')
        def admin_panel():
            return "Admin panel"
    """
    from functools import wraps
    from flask import abort
    from flask_login import current_user

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
