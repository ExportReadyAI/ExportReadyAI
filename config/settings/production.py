"""
Django Production Settings for ExportReady.AI
"""

import dj_database_url
from .base import *  # noqa: F401, F403

DEBUG = env.bool("DEBUG", default=False)  # noqa: F405

# Railway-specific: Get allowed hosts from environment
RAILWAY_STATIC_URL = env("RAILWAY_STATIC_URL", default="")  # noqa: F405
RAILWAY_PUBLIC_DOMAIN = env("RAILWAY_PUBLIC_DOMAIN", default="")  # noqa: F405

if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)  # noqa: F405
    ALLOWED_HOSTS.append(f"{RAILWAY_PUBLIC_DOMAIN}.railway.app")  # noqa: F405

# Also allow Railway internal domains
ALLOWED_HOSTS.extend([  # noqa: F405
    ".railway.app",
    ".up.railway.app",
])

# Database Configuration with Railway PostgreSQL
if env("DATABASE_URL", default=None):  # noqa: F405
    DATABASES["default"] = dj_database_url.config(  # noqa: F405
        default=env("DATABASE_URL"),  # noqa: F405
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS Settings - Railway provides HTTPS
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static Files with WhiteNoise
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"  # noqa: F405

# CORS - Restrict to specific origins in production
CORS_ALLOW_ALL_ORIGINS = False

# Add Railway domain to CORS if available
if RAILWAY_PUBLIC_DOMAIN:
    CORS_ALLOWED_ORIGINS.append(f"https://{RAILWAY_PUBLIC_DOMAIN}")  # noqa: F405
    CORS_ALLOWED_ORIGINS.append(f"https://{RAILWAY_PUBLIC_DOMAIN}.railway.app")  # noqa: F405

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

