from typing import Any, Dict

from django.conf import settings

from django_seriously.utils.settings import AppSettings

DEFAULTS: Dict[str, Any] = {
    "AUTH_TOKEN_SCOPES": [],
    "AUTH_TOKEN_MODEL": "django_seriously.authtoken.models.Token",
}

IMPORT_STRINGS = ["AUTH_TOKEN_MODEL"]

seriously_settings = AppSettings(
    user_settings=getattr(settings, "SERIOUSLY_SETTINGS", {}),
    defaults=DEFAULTS,
    import_strings=IMPORT_STRINGS,
)
