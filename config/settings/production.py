"""
Django Production Settings for ExportReady.AI
"""

from .base import *  # noqa: F401, F403

DEBUG = False

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS Settings
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CORS - Restrict to specific origins in production
CORS_ALLOW_ALL_ORIGINS = False

# Logging - Add file handler for production
LOGGING["handlers"]["file"] = {  # noqa: F405
    "class": "logging.FileHandler",
    "filename": BASE_DIR / "logs" / "django.log",  # noqa: F405
    "formatter": "verbose",
}
LOGGING["root"]["handlers"] = ["console", "file"]  # noqa: F405

# Sentry Configuration (optional)
SENTRY_DSN = env("SENTRY_DSN", default=None)  # noqa: F405
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

