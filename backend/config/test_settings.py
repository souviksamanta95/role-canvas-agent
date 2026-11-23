"""Settings for tests: dummy env defaults and an in-memory SQLite database.

No real secrets, Postgres or Redis are needed. Policy logic is database-agnostic;
the Postgres-specific parts (datasets schema, seed tables) are verified in Docker.
"""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-a-secret")
os.environ.setdefault("JWT_SIGNING_KEY", "test-only-jwt-signing-key-not-a-secret-0123456789")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")

from config.settings import *  # noqa: E402, F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
GOOGLE_OAUTH_CLIENT_ID = "test-client-id.apps.googleusercontent.com"
ALLOWED_EMAIL_DOMAINS = []
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": {"auth": "1000/min"}}  # noqa: F405

import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

STATIC_ROOT = Path(tempfile.mkdtemp(prefix="rolecanvas-static-"))
