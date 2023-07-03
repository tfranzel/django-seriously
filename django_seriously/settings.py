from typing import Any, Dict

from django.conf import settings

from django_seriously.utils.settings import AppSettings

DEFAULTS: Dict[str, Any] = {
    "AUTH_TOKEN_SCOPES": [],
    "AUTH_TOKEN_MODEL": "django_seriously.authtoken.models.Token",
    "MAKE_PASSWORD": "django_seriously.authtoken.utils.make_password",
    "CHECK_PASSWORD_REHASH": "django_seriously.authtoken.utils.check_password_rehash",
}

IMPORT_STRINGS = ["AUTH_TOKEN_MODEL", "MAKE_PASSWORD", "CHECK_PASSWORD_REHASH"]

seriously_settings = AppSettings(
    user_settings=getattr(settings, "SERIOUSLY_SETTINGS", {}),
    defaults=DEFAULTS,
    import_strings=IMPORT_STRINGS,
)
