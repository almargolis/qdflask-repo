# qdflask-repo

Reusable Flask integration packages for the QuickDev ecosystem.

## Packages

### qdflask — Data Layer (priority 10)
SQLAlchemy database instance and User model. This is the data foundation that all other packages build on.

```python
from qdflask import init_qdflask
from qdflask.models import db, User

init_qdflask(app, db_path='passwords.db')
```

### qdflaskauth — Authentication (priority 15)
Flask-Login integration, role-based access control, user management UI, and CLI tools. Depends on qdflask.

```python
from qdflaskauth import init_qdflaskauth

init_qdflaskauth(app, roles=['admin', 'editor', 'reader'])
```

When `enabled=False`, the app runs in **read-only mode**: no login UI, `@login_required` routes return 403.

### qdflaskemail — Email Notifications (priority 20)
Email notification service wrapping qdemail. When disabled, all functions silently no-op.

```python
from qdflaskemail import init_qdflaskemail, send_email, send_to_admins

init_qdflaskemail(app, config={'enabled': True})
```

### qdflaskapi — API Key Authentication (priority 25)
API key model, Bearer token validation middleware, and key management routes. Depends on qdflask and qdflaskauth.

```python
from qdflaskapi import init_qdflaskapi

init_qdflaskapi(app, config={
    'enabled': True,
    'all_users_can_generate_api_keys': False,
    'is_api': False,
})
```

**Configuration:**
- `enabled` — Enable API key system (default: `False`)
- `all_users_can_generate_api_keys` — All users can create keys vs. per-user permission (default: `False`)
- `is_api` — API-only mode: validate Bearer token on all routes, not just `/api/*` (default: `False`)

**Routes:** `GET/POST /api/keys`, `POST /api/keys/<id>/hold`, `POST /api/keys/<id>/activate`, `DELETE /api/keys/<id>`

### qdimages — Image Management (priority 50)
Content-addressed image storage with xxHash deduplication, web-based editor (crop, resize, brightness, background removal), metadata tracking, and REST API.

### qdcomments — Commenting System (priority 50)
Threaded commenting with moderation, content filtering (blocked words, HTML sanitization, markdown), and admin tools.

## Installation

```bash
pip install -e ./qdflask
pip install -e ./qdflaskauth
pip install -e ./qdflaskemail
pip install -e ./qdflaskapi
pip install -e ./qdimages
pip install -e ./qdcomments
```

## Configuration (qd_conf.toml)

Each package declares a `qd_conf.toml` that defines configuration questions and an `init_function` with a priority. QuickDev's qdstart reads these to auto-wire packages into the Flask app factory. Packages initialize in priority order:

| Priority | Package | Init function |
|---|---|---|
| 10 | qdflask | `init_qdflask(app, db_path)` |
| 15 | qdflaskauth | `init_qdflaskauth(app, enabled, roles, login_view)` |
| 20 | qdflaskemail | `init_qdflaskemail(app, config)` |
| 25 | qdflaskapi | `init_qdflaskapi(app, config)` |
| 50 | qdimages | `init_image_manager(app, config_dict)` |
| 50 | qdcomments | `init_comments(app, config)` |

## Repository Structure

```
qdflask-repo/
├── qdflask/src/qdflask/             # Data layer
├── qdflaskauth/src/qdflaskauth/     # Authentication
├── qdflaskemail/src/qdflaskemail/   # Email notifications
├── qdflaskapi/src/qdflaskapi/       # API key authentication
├── qdimages/src/qdimages/           # Image management
├── qdcomments/src/qdcomments/       # Comments
├── qdflask_tests/
├── qdflaskauth_tests/
├── qdflaskemail_tests/
├── qdflaskapi_tests/
├── qdimages_tests/
├── ai_skills.md                     # AI agent integration guide
└── CLAUDE.md                        # Claude Code project instructions
```

## Running Tests

```bash
pytest qdflask_tests/ qdflaskauth_tests/ qdflaskemail_tests/ qdflaskapi_tests/
```

## Dependencies

All packages depend on `qdbase` for configuration management and validation. Additional dependencies:
- **qdflask**: Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug
- **qdflaskauth**: Flask, Flask-Login, qdflask
- **qdflaskemail**: Flask, qdflask, qdemail
- **qdflaskapi**: Flask, Flask-Login, qdflask
- **qdimages**: Pillow, xxhash, PyYAML, rembg
- **qdcomments**: Flask, Flask-Login, PyYAML, Markdown

## Integration

These packages integrate through the QuickDev qdstart plugin system. Each package declares its configuration in `qd_conf.toml` and is auto-wired into the generated Flask application factory.

See `ai_skills.md` for detailed integration patterns and code examples.

## License

MIT
