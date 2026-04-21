import os
from pathlib import Path
from corsheaders.defaults import default_headers


def _load_env_file(base_dir: Path) -> None:
    env_file = base_dir / ".env"
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _get_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


BASE_DIR = Path(__file__).resolve().parents[2]
_load_env_file(BASE_DIR)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key-change-me")
DEBUG = _get_bool(os.getenv("DEBUG"), False)
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "*").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.gateway",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "apps.gateway.middleware.RequestContextMiddleware",
    "apps.gateway.middleware.RateLimitMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DB_ENGINE = os.getenv("DB_ENGINE", "django.db.backends.postgresql")
if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.getenv("DB_NAME", "student_housing_gateway_db"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}

CORS_ALLOW_ALL_ORIGINS = _get_bool(os.getenv("CORS_ALLOW_ALL_ORIGINS"), False)
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
    ).split(",")
    if origin.strip()
]
CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-admin-id",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "api-gateway-cache",
    }
}

GATEWAY_UPSTREAM_TIMEOUT_SECONDS = max(20.0, float(os.getenv("GATEWAY_UPSTREAM_TIMEOUT_SECONDS", "20")))

GATEWAY_SERVICE_MAP = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:8001/auth"),
    "users": os.getenv("USER_SERVICE_URL", "http://localhost:8002/users"),
    "housing": os.getenv("HOUSING_SERVICE_URL", "http://localhost:8003/housing"),
    "search": os.getenv("SEARCH_SERVICE_URL", "http://localhost:8004/search"),
    "bookings": os.getenv("BOOKING_SERVICE_URL", "http://localhost:8005/bookings"),
    "payments": os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8006/payments"),
    "notifications": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8007/notifications"),
    "ai": os.getenv("AI_SERVICE_URL", "http://localhost:8008/ai"),
    "roommate": os.getenv("ROOMMATE_SERVICE_URL", "http://localhost:8012"),
    "moderation": os.getenv("MODERATION_SERVICE_URL", "http://localhost:8009/moderation"),
    "admin": os.getenv("ADMIN_SERVICE_URL", "http://localhost:8010/admin"),
    "reports": os.getenv("REPORTING_SERVICE_URL", "http://localhost:8011/reports"),
}

GATEWAY_DEFAULT_RATE_LIMITS = {
    "ip": {
        "limit_per_minute": int(os.getenv("RATE_LIMIT_IP_PER_MINUTE", "120")),
        "burst_limit": int(os.getenv("RATE_LIMIT_IP_BURST", "30")),
    },
    "user": {
        "limit_per_minute": int(os.getenv("RATE_LIMIT_USER_PER_MINUTE", "240")),
        "burst_limit": int(os.getenv("RATE_LIMIT_USER_BURST", "60")),
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "gateway.request": {
            "handlers": ["console"],
            "level": os.getenv("GATEWAY_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
