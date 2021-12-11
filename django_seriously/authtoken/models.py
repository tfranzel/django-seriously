from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from django_seriously.settings import seriously_settings
from django_seriously.utils.models import BaseModel


class Token(BaseModel):
    name = models.CharField(max_length=25, blank=True)
    key = models.CharField(_("Key"), max_length=128)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="auth_tokens",
        on_delete=models.CASCADE,
    )
    scopes = models.CharField(
        blank=True,
        max_length=50,
        help_text=(
            f"comma-separated list of scopes. choices are "
            f"{','.join(seriously_settings.AUTH_TOKEN_SCOPES)}."
        ),
    )

    @cached_property
    def scope_list(self):
        return self.scopes.split(",")

    def clean(self) -> None:
        super().clean()
        if isinstance(self.scopes, (list, tuple)):
            scopes = self.scopes
        elif isinstance(self.scopes, str):
            scopes = self.scopes.split(",")
        else:
            raise ValidationError({"scopes": "invalid scopes input"})

        valid_scopes = seriously_settings.AUTH_TOKEN_SCOPES
        if valid_scopes and not all([s in valid_scopes for s in scopes]):
            raise ValidationError(
                {"scopes": f"invalid scope choices. valid choices are: {valid_scopes}"}
            )
        self.scopes = ",".join(scopes)

    class Meta:
        abstract = "django_seriously.authtoken" not in settings.INSTALLED_APPS
