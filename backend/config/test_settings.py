"""Settings for tests: supplies dummy env defaults so no real secrets or DB are needed."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-a-secret")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")

from config.settings import *  # noqa: E402, F403
