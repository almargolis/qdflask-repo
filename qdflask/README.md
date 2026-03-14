# qdflask - QuickDev Flask Data Layer

Provides the SQLAlchemy database instance and User model for QuickDev Flask applications. This is the data foundation that other packages (qdflaskauth, qdflaskemail, qdcomments) build on.

## Features

- SQLAlchemy database instance (`db`)
- User model with password hashing, roles, and email fields
- Simple initialization with `init_qdflask(app)`

## Installation

```bash
pip install -e ./qdflask
```

## Quick Start

```python
from flask import Flask
from qdflask import init_qdflask
from qdflask.models import db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Initialize data layer
init_qdflask(app, db_path='passwords.db')
```

## Authentication

Authentication routes, Flask-Login integration, and user management UI are provided by the separate **qdflaskauth** package:

```bash
pip install -e ./qdflaskauth
```

```python
from qdflaskauth import init_qdflaskauth

init_qdflask(app)
init_qdflaskauth(app, roles=['admin', 'editor', 'viewer'])
```

See the [qdflaskauth README](../qdflaskauth/README.md) for full details.

## User Model

The `User` model provides:

- `username`, `email_address`, `email_verified`
- `password_hash` (hashed with Werkzeug)
- `role` (e.g., 'admin', 'editor', 'reader')
- `is_active`, `created_at`, `last_login`
- `comment_style`, `moderation_level` (for qdcomments integration)

### Methods

```python
user.set_password('secret123')
user.check_password('secret123')  # True
user.is_admin()                   # True if role == 'admin'
user.has_role('admin', 'editor')  # True if role matches any

User.get_by_username('john')
User.get_by_email('john@example.com')
User.get_all_active()
User.get_verified_admins()
```

## Email Notifications

Email notifications are provided by the separate **qdflaskemail** package. See the [qdflaskemail README](../qdflaskemail/README.md).

## Security Notes

- Passwords are hashed using Werkzeug's `generate_password_hash()`
- Never store plain text passwords
- Use a strong `SECRET_KEY` in production
