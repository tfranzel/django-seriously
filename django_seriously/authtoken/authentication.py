import base64
import uuid
from typing import TYPE_CHECKING, Optional

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.permissions import BasePermission

from django_seriously.settings import seriously_settings

if TYPE_CHECKING:
    from django_seriously.authtoken.models import Token


class TokenAuthentication(BaseAuthentication):
    """
    TODO
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            msg = _("Invalid token header. No credentials provided.")
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _("Invalid token header. Token string should not contain spaces.")
            raise exceptions.AuthenticationFailed(msg)

        try:
            token_str = auth[1].decode()
        except UnicodeError:
            msg = _(
                "Invalid token header. Token string should not contain invalid characters."
            )
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token_str)

    def authenticate_credentials(self, token_str):
        model = seriously_settings.AUTH_TOKEN_MODEL

        try:
            token_bytes = base64.urlsafe_b64decode(token_str)
            if len(token_bytes) != 32:
                raise ValueError()
            token_id = uuid.UUID(bytes=token_bytes[:16], version=4)
            raw_token = token_bytes[16:]
        except ValueError:
            raise exceptions.AuthenticationFailed(_("Invalid token."))

        try:
            token: "Token" = model.objects.select_related("user").get(id=token_id)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_("Invalid token."))

        if not check_password(password=raw_token, encoded=token.key):  # type: ignore
            raise exceptions.AuthenticationFailed(_("Invalid token."))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_("User inactive or deleted."))

        return token.user, token

    def authenticate_header(self, request):
        return self.keyword


class TokenHasScope(BasePermission):
    """Derived from django-oauth-toolkit's TokenHasScope"""

    def has_permission(self, request, view):
        token: Optional["Token"] = request.auth

        if not token:
            return False

        if hasattr(token, "scope"):
            required_scopes = self.get_scopes(request, view)
            return all(r in token.scope_list for r in required_scopes)

        assert False, (
            "TokenHasScope requires the`django_seriously.authtoken.TokenAuthentication` "
            "authentication class to be used."
        )

    def get_scopes(self, request, view):
        try:
            return getattr(view, "required_scopes")
        except AttributeError:
            raise ImproperlyConfigured(
                "TokenHasScope requires the view to define the required_scopes attribute"
            )
