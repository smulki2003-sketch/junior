from .base import *  # noqa: F401,F403


DEBUG = False
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}
AUTH_SERVICE_JWT_SECRET = "test-jwt-secret"
INTERNAL_SERVICE_TOKEN = "test-service-token"
