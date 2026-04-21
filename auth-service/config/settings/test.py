from .base import *  # noqa: F401,F403


DEBUG = False
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EXPOSE_PASSWORD_RESET_TOKEN = True
JWT_ACCESS_TTL_MINUTES = 30
JWT_REFRESH_TTL_DAYS = 1

