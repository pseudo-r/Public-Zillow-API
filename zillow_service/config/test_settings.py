import os as _os

import environ as _environ

_os.environ.setdefault("SECRET_KEY", "test-only-not-for-production")
from .settings import *  # noqa: E402, F403

SECRET_KEY = "test-only-not-for-production"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

# Opt into a separate test database explicitly; never use production DATABASE_URL.


if _os.environ.get("TEST_DATABASE_URL"):
    DATABASES = {"default": _environ.Env.db_url_config(_os.environ["TEST_DATABASE_URL"])}
