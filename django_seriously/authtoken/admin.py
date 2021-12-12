from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.utils.translation import gettext_lazy as _

from django_seriously.authtoken.models import Token
from django_seriously.authtoken.utils import generate_token


class TokenAdmin(ModelAdmin):
    list_display = (
        "id",
        "user",
        "name",
        "scopes",
    )
    readonly_fields = ("id", "key")

    def save_model(self, request, obj: Token, form, change):
        if not change:
            token = generate_token()
            self.message_user(
                request=request,
                message=_(
                    'New bearer token is "{}". This can only be viewed once!'
                ).format(token.encoded_bearer),
                level=messages.WARNING,
            )
            obj.id = token.id
            obj.key = token.key
        return super().save_model(request, obj, form, change)


if "django_seriously.authtoken" in settings.INSTALLED_APPS:
    admin.site.register(Token, TokenAdmin)
