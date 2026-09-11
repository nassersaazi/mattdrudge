from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = ["*"]

# Hash static filenames so stale CSS/JS is never served from browser cache.
STORAGES["staticfiles"]["BACKEND"] = (
    "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
)

try:
    from .local import *  # noqa: F401,F403
except ImportError:
    SECRET_KEY = "insecure-prod-key"
