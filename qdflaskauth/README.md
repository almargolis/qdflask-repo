# qdflaskauth - QuickDev Flask Authentication

Flask authentication routes, role-based access control, user management UI, and CLI tools. Depends on `qdflask` for the data layer (SQLAlchemy db + User model).

## Features

- User authentication with Flask-Login
- Role-based access control with customizable roles
- User management interface (admin only)
- CLI commands for user management
- Read-only mode (disable auth routes while keeping `@login_required` functional)

## Installation

```bash
pip install -e ./qdflask       # data layer (must be installed first)
pip install -e ./qdflaskauth   # auth routes
```

## Quick Start

```python
from flask import Flask
from qdflask import init_qdflask
from qdflaskauth import init_qdflaskauth, create_admin_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Initialize data layer, then auth
init_qdflask(app)
init_qdflaskauth(app, roles=['admin', 'editor', 'viewer'])
```

## Protecting Routes

```python
from flask_login import login_required
from qdflaskauth import require_role

@app.route('/admin')
@login_required
@require_role('admin')
def admin_panel():
    return "Admin panel"

@app.route('/edit')
@login_required
@require_role('admin', 'editor')
def edit_content():
    return "Edit content"
```

## Read-Only Mode

When `enabled=False`, auth routes are not registered but `@login_required` still works (returns 403 JSON instead of redirecting to login):

```python
init_qdflaskauth(app, enabled=False)
# Routes with @login_required will return {"error": "Authentication is disabled"}, 403
# No /auth/* routes are available
# No admin user is seeded
```

## Routes Provided

When enabled, the `auth_bp` blueprint provides:

- `/auth/login` - Login page (GET) and login processing (POST)
- `/auth/logout` - Logout (requires login)
- `/auth/users` - User management page (admin only)
- `/auth/users/add` - Add new user (admin only)
- `/auth/users/edit/<id>` - Edit user (admin only)
- `/auth/users/delete/<id>` - Delete user (admin only)

## CLI Commands

### Initialize Database and Create Admin User

```bash
python -m qdflaskauth.cli init --app myapp:app --admin-password secret123
```

### Create Additional Users

```bash
python -m qdflaskauth.cli create-user --app myapp:app --username john --password secret --role editor
```

### List All Users

```bash
python -m qdflaskauth.cli list-users --app myapp:app
```

## Configuration

```python
# Custom roles (must include 'admin')
init_qdflaskauth(app, roles=['admin', 'editor', 'viewer'])

# Custom login view
init_qdflaskauth(app, login_view='custom_auth.login')

# Disable auth routes (read-only mode)
init_qdflaskauth(app, enabled=False)
```
