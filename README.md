# qdflask

Reusable Flask integration packages for web applications.

## Packages

### qdflask - User Authentication
Complete user authentication with Flask-Login, role-based access control, user management UI, CLI tools, and optional email notifications.

```bash
pip install -e ./qdflask
```

### qdimages - Image Management
Content-addressed image storage with xxHash deduplication, web-based editor (crop, resize, brightness, background removal), metadata tracking, and REST API.

```bash
pip install -e ./qdimages
```

### qdcomments - Commenting System
Threaded commenting with moderation, content filtering (blocked words, HTML sanitization, markdown), and admin tools.

```bash
pip install -e ./qdcomments
```

## Dependencies

All packages depend on `qdbase` for configuration management and check/validation framework.

## Integration

These packages integrate through the QuickDev qdstart plugin system. Each package declares its configuration in `qd_conf.toml` and is auto-wired into the generated Flask application factory.

See individual package READMEs for detailed documentation.

## License

MIT
