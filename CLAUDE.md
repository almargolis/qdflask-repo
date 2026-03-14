# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a monorepo containing reusable Flask packages for the QuickDev ecosystem:

- **qdflask** — Data layer (SQLAlchemy db instance, User model)
- **qdflaskauth** — Authentication (Flask-Login, RBAC, user management UI, CLI, read-only mode)
- **qdflaskemail** — Email notifications (wraps qdemail, admin notifications, enabled/disabled flag)
- **qdimages** — Image management (content-addressed storage with xxHash, web editor, REST API)
- **qdcomments** — Threaded commenting (moderation, content filtering, admin tools)

Each package lives under `<pkg>/src/<pkg>/` with its own `setup.py`. Tests are in `qdflask_tests/`, `qdflaskauth_tests/`, `qdflaskemail_tests/`, and `qdimages_tests/`.

## Commands

### Install packages (editable mode)
```bash
pip install -e ./qdflask
pip install -e ./qdflaskauth
pip install -e ./qdflaskemail
pip install -e ./qdimages
pip install -e ./qdcomments
```

### Run tests
```bash
pytest qdflask_tests/
pytest qdflaskauth_tests/
pytest qdflaskemail_tests/
pytest qdflask_tests/ qdflaskauth_tests/ qdflaskemail_tests/  # all at once
```

## Architecture

### Database ownership
- **qdflask** owns the SQLAlchemy `db` instance and `User` model (`qdflask.models`)
- **qdcomments** imports `db` and `User` from `qdflask.models` (shared database)
- **qdimages** creates its own db but can accept an existing one via `use_existing_db()`

### Plugin system (qd_conf.toml)
Each package declares a `qd_conf.toml` that defines configuration questions and an `init_function` with a priority. QuickDev's qdstart reads these to auto-wire packages into the Flask app factory:
- qdflask: priority **10** (initializes first — data layer)
- qdflaskauth: priority **15** (auth layer, depends on qdflask)
- qdflaskemail: priority **20**
- qdimages, qdcomments: priority **50**

### Initialization pattern
Each package exports an `init_*()` function that takes `(app, config)`, registers blueprints, and creates tables:
- `qdflask.init_qdflask(app, db_path='passwords.db')` — initializes db, creates tables
- `qdflaskauth.init_qdflaskauth(app, enabled=True, roles=[...], login_view='auth.login')` — registers `auth_bp` at `/auth`
- `qdflaskemail.init_qdflaskemail(app, config)` — sets email enabled/disabled
- `qdimages.init_image_manager(app, config_dict)` — registers `image_bp`
- `qdcomments.init_comments(app, config)` — registers `comments_bp` at `/comments`

### Key cross-package integration
- The `User` model includes `comment_style` and `moderation_level` fields used by qdcomments
- qdcomments snapshots these values at comment-creation time (prevents retroactive permission changes)
- qdimages routes require `@login_required` from Flask-Login (set up by qdflaskauth)

### External dependencies
All packages depend on **qdbase** (not in this repo) for configuration (`qdconf`) and validation (`qdcheck`) utilities. **qdflaskemail** depends on **qdemail** for SMTP delivery. These sibling packages live in the QuickDev monorepo at `../quickdev/` (one level up from this repo in `/Users/almargolis/Projects/published/`).

## Test patterns
- Tests use in-memory SQLite (`sqlite:///:memory:`) or temp directories
- Fixtures create a Flask app with `app.app_context()` for database operations
- qdimages tests use `tempfile.TemporaryDirectory` for image storage

## Active refactoring plan
`add_api_support.md` describes a 5-phase plan to decompose qdflask into sub-packages (qdflaskemail, qdflaskauth) and add an API server package (qdflaskapi). No backward compatibility is required.

## ai_skills.md
`ai_skills.md` is a reference guide for AI agents building Flask applications **that consume** these packages. When making changes that affect how users integrate or use the packages (new APIs, changed init signatures, new config options, etc.), update `ai_skills.md` to reflect those changes.

## When extending the User model
If the application needs user fields beyond what qdflask provides, prefer creating a **separate model with a foreign key to User.id** rather than modifying qdflask's User model directly. See `ai_skills.md` for details and code examples.
