# qdflaskemail - QuickDev Flask Email Notifications

A standalone email notification service for QuickDev Flask applications. Wraps the `qdemail` package and provides admin notification helpers with an `enabled` config flag that allows email to silently no-op when disabled.

## Installation

```bash
pip install -e ./qdflaskemail
```

## Quick Start

```python
from flask import Flask
from qdflask import init_auth
from qdflaskemail import init_qdflaskemail, send_to_admins, send_email

app = Flask(__name__)

# Initialize auth (required - provides User model)
init_auth(app)

# Initialize email
init_qdflaskemail(app)

# Send email to verified admins
send_to_admins(
    subject="Important Alert",
    body="Something happened that requires your attention."
)

# Send email to specific recipients
send_email(
    subject="Welcome",
    recipients=["user@example.com"],
    body="Welcome to our application!"
)
```

## Configuration

### Disabling Email

Set `QDFLASKEMAIL_ENABLED = False` in your Flask config to silently disable all email sending. All functions will return `False` (send functions) or `[]` (getters) without calling qdemail.

```python
app.config['QDFLASKEMAIL_ENABLED'] = False
```

Or pass it during initialization:

```python
init_qdflaskemail(app, config={'enabled': False})
```

### SMTP Configuration

Email configuration uses two files:

1. **conf/email.yaml** - SMTP server settings (safe to commit)
2. **.env** - SMTP password (NEVER commit)

#### Step 1: Create conf/email.yaml

Copy the example and customize for your SMTP provider:

```bash
cp qdflask/conf/email.yaml.example conf/email.yaml
```

Example `conf/email.yaml`:

```yaml
# SMTP Server Configuration
server: smtp-relay.brevo.com
port: 587
use_tls: true
use_ssl: false

# SMTP Authentication
username: your-email@example.com

# Default sender for outgoing emails
default_sender: noreply@yourdomain.com
```

#### Step 2: Add Password to .env

```bash
# conf/.env
SMTP_PW=your-smtp-password-or-api-key
```

### SMTP Provider Examples

#### Brevo (Recommended - Free Tier: 300 emails/day)

```yaml
# conf/email.yaml
server: smtp-relay.brevo.com
port: 587
use_tls: true
username: your-brevo-email@example.com
default_sender: noreply@yourdomain.com
```

```bash
# .env
SMTP_PW=your-brevo-smtp-key
```

#### SendGrid (Free Tier: 100 emails/day)

```yaml
# conf/email.yaml
server: smtp.sendgrid.net
port: 587
use_tls: true
username: apikey  # Literal string "apikey"
default_sender: noreply@yourdomain.com
```

```bash
# .env
SMTP_PW=your-sendgrid-api-key
```

#### Gmail (Not Recommended for Production)

```yaml
# conf/email.yaml
server: smtp.gmail.com
port: 587
use_tls: true
username: your-email@gmail.com
default_sender: your-email@gmail.com
```

```bash
# .env
SMTP_PW=your-app-password  # Not your regular password!
```

## Email Verification

Users have an `email_verified` field ('Y' or 'N') that controls whether they receive routine notifications:

- Only users with `email_verified='Y'` receive routine emails
- Admins can set this field when editing users
- Users can have a blank `email_address` to prevent all emails
- Use `User.get_verified_admins()` to get admins who should receive notifications

## API

### `init_qdflaskemail(app, config=None)`

Initialize the email service. Sets `QDFLASKEMAIL_ENABLED` default in app config.

### `send_email(subject, recipients, body, sender=None)`

Send an email to specific recipients. Returns `False` when disabled.

### `send_to_admins(subject, body, sender=None)`

Send email to all verified admin users. Returns `False` when disabled or no verified admins exist.

### `get_verified_admin_emails()`

Get list of verified admin email addresses. Returns `[]` when disabled.
