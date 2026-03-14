"""
qdflaskauth.auth - Authentication blueprint

Provides routes for login, logout, and user management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user, login_user, logout_user
from qdflask.models import User, db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth',
                    template_folder='templates')


def _api_keys_display_state():
    """Return (show, editable, forced_value) for the can_generate_api_keys field.

    Visibility rules:
    - API disabled: hidden, forced False
    - API enabled + all users can generate: hidden, forced True
    - API enabled + not all users: shown, editable, no forced value
    """
    api_enabled = current_app.config.get('QDFLASKAPI_ENABLED', False)
    all_users = current_app.config.get('QDFLASKAPI_ALL_USERS_CAN_GENERATE_API_KEYS', False)
    if not api_enabled:
        return False, False, False
    if all_users:
        return False, False, True
    return True, True, None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.

    GET: Display login form
    POST: Process login credentials
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.get_by_username(username)
        if user and user.is_active and user.check_password(password):
            login_user(user)
            user.update_last_login()

            # Redirect to next page or home
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))

        return render_template('qdflaskauth/login.html', error="Invalid credentials"), 401

    return render_template('qdflaskauth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('index'))


@auth_bp.route('/users')
@login_required
def list_users():
    """List all users (admin only)."""
    if not current_user.is_admin():
        return "Access denied", 403

    users = User.get_all()
    roles = current_app.config.get('QDFLASK_ROLES', ['admin', 'editor'])
    show_api_keys, _, _ = _api_keys_display_state()

    return render_template('qdflaskauth/user_management.html', users=users, roles=roles,
                           show_api_keys=show_api_keys)


@auth_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    """Add a new user (admin only)."""
    if not current_user.is_admin():
        return "Access denied", 403

    roles = current_app.config.get('QDFLASK_ROLES', ['admin', 'editor'])
    show_api_keys, api_keys_editable, forced_api_keys = _api_keys_display_state()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'editor')

        # Validation
        if not username or not password:
            return render_template('qdflaskauth/add_user.html',
                                   error="Username and password are required",
                                   roles=roles, show_api_keys=show_api_keys,
                                   api_keys_editable=api_keys_editable)

        if User.get_by_username(username):
            return render_template('qdflaskauth/add_user.html',
                                   error="Username already exists",
                                   roles=roles, show_api_keys=show_api_keys,
                                   api_keys_editable=api_keys_editable)

        if len(password) < 6:
            return render_template('qdflaskauth/add_user.html',
                                   error="Password must be at least 6 characters",
                                   roles=roles, show_api_keys=show_api_keys,
                                   api_keys_editable=api_keys_editable)

        if role not in roles:
            role = 'editor'

        # Create user
        new_user = User(username=username, role=role)
        new_user.set_password(password)

        if forced_api_keys is not None:
            new_user.can_generate_api_keys = forced_api_keys
        else:
            new_user.can_generate_api_keys = request.form.get('can_generate_api_keys') == 'on'

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('auth.list_users'))

    return render_template('qdflaskauth/add_user.html', roles=roles,
                           show_api_keys=show_api_keys,
                           api_keys_editable=api_keys_editable)


@auth_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit an existing user (admin only)."""
    if not current_user.is_admin():
        return "Access denied", 403

    user = User.get(user_id)
    if not user:
        return "User not found", 404

    roles = current_app.config.get('QDFLASK_ROLES', ['admin', 'editor'])
    show_api_keys, api_keys_editable, forced_api_keys = _api_keys_display_state()

    if request.method == 'POST':
        role = request.form.get('role', 'editor')
        is_active = request.form.get('is_active') == 'on'
        new_password = request.form.get('new_password')

        if role in roles:
            user.role = role

        user.is_active = is_active

        if forced_api_keys is not None:
            user.can_generate_api_keys = forced_api_keys
        else:
            user.can_generate_api_keys = request.form.get('can_generate_api_keys') == 'on'

        if new_password:
            if len(new_password) < 6:
                return render_template('qdflaskauth/edit_user.html',
                                       user=user,
                                       roles=roles,
                                       show_api_keys=show_api_keys,
                                       api_keys_editable=api_keys_editable,
                                       error="Password must be at least 6 characters")
            user.set_password(new_password)

        db.session.commit()

        return redirect(url_for('auth.list_users'))

    return render_template('qdflaskauth/edit_user.html', user=user, roles=roles,
                           show_api_keys=show_api_keys,
                           api_keys_editable=api_keys_editable)


@auth_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user (admin only)."""
    if not current_user.is_admin():
        return "Access denied", 403

    # Prevent deleting yourself
    if user_id == current_user.id:
        return "Cannot delete your own account", 400

    user = User.get(user_id)
    if not user:
        return "User not found", 404

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('auth.list_users'))
