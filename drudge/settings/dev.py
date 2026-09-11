from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

try:
    from .local import *  # noqa: F401,F403
except ImportError:
    SECRET_KEY = "insecure-dev-key"
