# Flask with QuickDev Skill Reference

Use this reference when building Flask applications with the QuickDev toolkit.

## Packages

### qdflask - Data Layer

**What it provides**: SQLAlchemy database instance and User model. This is the data foundation that other packages build on.

**Integration**:
```python
from qdflask import init_qdflask
from qdflask.models import db, User

init_qdflask(app, db_path='passwords.db')
```

**User model fields**:
- `id`, `username`, `email_address`, `email_verified`
- `password_hash`, `role`, `is_active`
- `created_at`, `last_login`
- `comment_style`, `moderation_level` (for qdcomments integration)
- `can_generate_api_keys` (for qdflaskapi integration)

**User model methods**: `set_password()`, `check_password()`, `is_admin()`, `is_editor()`, `has_role()`, `get_by_username()`, `get_by_email()`, `get_all_active()`, `get_verified_admins()`

### qdflaskauth - Authentication

**What it provides**: Flask-Login integration, role-based access control, user management UI, CLI tools, and read-only mode. Depends on qdflask for the data layer.

**Integration**:
```python
from qdflask import init_qdflask
from qdflaskauth import init_qdflaskauth, create_admin_user

# Initialize data layer first, then auth
init_qdflask(app)
init_qdflaskauth(app, roles=['admin', 'editor', 'reader'])
```

**Read-only mode** (disable auth routes while `@login_required` still works):
```python
init_qdflaskauth(app, enabled=False)
# Routes with @login_required return {"error": "Authentication is disabled"}, 403
# No /auth/* routes, no admin seeded
```

**Routes**: `/auth/login`, `/auth/logout`, `/auth/users` (admin CRUD)

**Protection patterns**:
```python
from flask_login import login_required
from qdflaskauth import require_role

@app.route('/admin')
@login_required
@require_role('admin')
def admin_panel(): ...

@app.route('/edit')
@login_required
@require_role('admin', 'editor')
def edit_content(): ...
```

### qdflaskemail - Email Notifications

**What it provides**: Email notification service wrapping qdemail, with admin notification helpers and an enabled/disabled config flag. When disabled, all functions silently no-op.

**Integration**:
```python
from qdflaskemail import init_qdflaskemail, send_email, send_to_admins

init_qdflaskemail(app)
# or disable: init_qdflaskemail(app, config={'enabled': False})
```

**Public API**:
- `send_email(subject, recipients, body, sender=None)` — send to specific recipients
- `send_to_admins(subject, body, sender=None)` — send to verified admin users
- `get_verified_admin_emails()` — list verified admin email addresses

**Disabling**: Set `QDFLASKEMAIL_ENABLED = False` in app config — all functions return `False` or `[]` without calling qdemail.

### qdimages - Image Management

**What it provides**: Content-addressed image storage with xxHash dedup, web-based editor (crop, resize, brightness, background removal), metadata tracking, REST API with 16 endpoints.

**Integration**:
```python
from qdimages import init_image_manager

init_image_manager(app, {
    'IMAGES_BASE_PATH': './images',
    'MAX_CONTENT_LENGTH': 10 * 1024 * 1024
})
```

**Access points**: `/image-editor` (web UI), `/api/images/*` (REST API)

### qdflaskapi - API Key Authentication

**What it provides**: API key model, Bearer token validation middleware, and key management routes. Depends on qdflask for the data layer and qdflaskauth for login/roles.

**Integration**:
```python
from qdflask import init_qdflask
from qdflaskauth import init_qdflaskauth
from qdflaskapi import init_qdflaskapi

init_qdflask(app)
init_qdflaskauth(app, roles=['admin', 'editor'])
init_qdflaskapi(app, config={
    'enabled': True,
    'all_users_can_generate_api_keys': False,
    'is_api': False,
})
```

**Config options**:
- `enabled` — Enable API key system (default: `False`)
- `all_users_can_generate_api_keys` — When `True`, every user can create keys; when `False`, only users with `can_generate_api_keys=True` (default: `False`)
- `is_api` — API-only mode: validate Bearer token on all routes, not just `/api/*` (default: `False`)

**Routes** (all require `@login_required`):
- `GET /api/keys` — List current user's keys (admins: `?user_id=N` to see another user's)
- `POST /api/keys` — Create a new key (requires `can_generate_api_keys`). JSON body: `{purpose, expires_at?}`. Returns full key string (only time it's shown).
- `POST /api/keys/<id>/hold` — Pause a key (owner or admin)
- `POST /api/keys/<id>/activate` — Reactivate a held key (owner or admin)
- `DELETE /api/keys/<id>` — Delete a key (owner or admin)

**Middleware**: Extracts `Authorization: Bearer <key>` header. On valid key, sets `g.current_api_user` and updates `last_used_at`. Returns `401` JSON for invalid/missing key on API routes.

**APIKey model fields**: `id`, `key`, `user_id`, `purpose`, `created_at`, `expires_at`, `status` ('a'=active, 'h'=hold), `last_used_at`, `created_by_ip`

### qdcomments - Commenting System

**What it provides**: Threaded commenting with moderation, content filtering (blocked words, HTML sanitization, markdown), and admin tools.

### Package Installation

All packages are installed automatically by qdstart when enabled. For manual installation:
```bash
pip install -e ./qdflask
pip install -e ./qdflaskauth
pip install -e ./qdflaskemail
pip install -e ./qdflaskapi
pip install -e ./qdimages
pip install -e ./qdcomments
```

## Handling Application-Specific User Data

When the application needs user information beyond what qdflask's User model provides (e.g., profile fields, preferences, app-specific attributes):

**STOP and ask the user**:
> "This application needs user data not in qdflask's User model (specifically: [list the fields]). How would you like to handle this?"
>
> 1. **Extend in this application** (recommended) - Create a separate model/table with a foreign key to qdflask's User.id.
>
> 2. **Modify qdflask's User model** - If this data is genuinely general-purpose and would benefit all projects.

### Option 1: Extend in the application (default recommendation)

```python
from qdbase import pdict, qdsqlite

profile = pdict.DbDictTable("user_profiles", is_rowid_table=True)
profile.add_column(pdict.Number("user_id", nullable=False, unique=True))
profile.add_column(pdict.Text("display_name"))
profile.add_column(pdict.Text("bio"))
```

Or with Flask-SQLAlchemy:

```python
class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False)
    display_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
```

## Dependencies

- `qdbase` - Foundation package (qdcheck, qdconf)
- Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug (qdflask)
- Flask, Flask-Login, qdflask (qdflaskauth)
- Flask, Flask-Login, qdflask (qdflaskapi)
- Pillow, xxhash, PyYAML, rembg (qdimages)

## Repository Structure

```
qdflask-repo/
├── qdflask/src/qdflask/             # Data layer package
├── qdflaskauth/src/qdflaskauth/     # Authentication package
├── qdflaskapi/src/qdflaskapi/       # API key authentication package
├── qdflaskemail/src/qdflaskemail/   # Email notifications package
├── qdimages/src/qdimages/           # Image management package
├── qdcomments/src/qdcomments/       # Comments package
├── qdflask_tests/
├── qdflaskauth_tests/
├── qdflaskemail_tests/
├── qdflaskapi_tests/
├── qdimages_tests/
└── README.md
```
