"""
Django Test Settings for ExportReady.AI
"""

from .fikribase import *  # noqa: F401, F403

DEBUG = False

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Use in-memory SQLite for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "DEBUG",
    },
}

# Shorter token lifetime for tests
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=5)  # noqa: F405
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = timedelta(minutes=10)  # noqa: F405

