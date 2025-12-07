"""
Django Development Settings for ExportReady.AI
"""

from .fikribase import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# CORS - Allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Development-specific apps
INSTALLED_APPS += [  # noqa: F405
    "django_extensions",
]

# Django Debug Toolbar
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
    INTERNAL_IPS = ["127.0.0.1"]

# Email Backend - Console for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Allow browsable API in development
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# Shorter token lifetime for development testing
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=60)  # noqa: F405
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = timedelta(days=1)  # noqa: F405

