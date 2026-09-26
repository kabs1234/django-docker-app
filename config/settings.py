import os
from pathlib import Path

TRUTHY_VALUES: frozenset[str] = frozenset({"1", "true", "yes", "on"})


def env_flag(name: str, default: str = "false") -> bool:
    """Return True when the environment variable holds a truthy value."""
    return os.environ.get(name, default).strip().lower() in TRUTHY_VALUES


def env_list(name: str, default: str) -> list[str]:
    """Split a comma-separated environment variable into a list of trimmed items."""
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


BASE_DIR: Path = Path(__file__).resolve().parent.parent

SECRET_KEY: str = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-secret-key-change-me")
DEBUG: bool = env_flag("DJANGO_DEBUG")
ALLOWED_HOSTS: list[str] = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

APP_NAME: str = os.environ.get("APP_NAME", "Django Docker App")
APP_ENV: str = os.environ.get("APP_ENV", "development")
PORT: str = os.environ.get("PORT", "8000")

INSTALLED_APPS: list[str] = [
    "web",
]

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    },
]

DATABASES: dict[str, dict[str, str]] = {}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}