import base64
import os
import uuid
from unittest import mock

import pytest
from django.contrib.auth.hashers import get_hasher
from django.contrib.auth.models import User
from django.urls import path
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.views import APIView

from django_seriously.authtoken.authentication import TokenAuthentication, TokenHasScope
from django_seriously.authtoken.models import Token
from django_seriously.authtoken.utils import TokenContainer, generate_token


class TestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        return Response("ok")


class TestAPIScopedView(APIView):
    permission_classes = [TokenHasScope]
    authentication_classes = [TokenAuthentication]
    required_scopes = ["test-scope1"]

    def get(self, request):
        return Response("ok")


urlpatterns = [
    path("u/", TestAPIView.as_view()),
    path("s/", TestAPIScopedView.as_view()),
]


def gen_token() -> tuple[Token, TokenContainer]:
    token_container = generate_token()
    token = Token.objects.create(
        id=token_container.id,
        key=token_container.key,
        user=User.objects.create_user("test@example.com"),
        name="test",
    )
    return token, token_container


@pytest.mark.urls(__name__)
@pytest.mark.django_db
def test_token_auth():
    token, token_container = gen_token()

    response = APIClient().get("/u/")
    assert response.status_code == 401

    response = APIClient().get(
        "/u/", HTTP_AUTHORIZATION=f"Bearer {token_container.encoded_bearer}"
    )
    assert response.status_code == 200


@pytest.mark.urls(__name__)
@pytest.mark.django_db
def test_unknown_token():
    token_id = uuid.uuid4()
    secret = os.urandom(16)
    raw_bearer_token = token_id.bytes + secret
    bearer = base64.urlsafe_b64encode(raw_bearer_token).decode()

    response = APIClient().get("/u/", HTTP_AUTHORIZATION=f"Bearer {bearer}")
    assert response.status_code == 401


@pytest.mark.urls(__name__)
@pytest.mark.django_db
def test_known_id_invalid_secret():
    _, token_container = gen_token()
    secret = os.urandom(16)
    raw_bearer_token = token_container.id.bytes + secret
    bearer = base64.urlsafe_b64encode(raw_bearer_token).decode()

    response = APIClient().get("/u/", HTTP_AUTHORIZATION=f"Bearer {bearer}")
    assert response.status_code == 401


@pytest.mark.urls(__name__)
@pytest.mark.django_db
@mock.patch(
    "django_seriously.settings.seriously_settings.AUTH_TOKEN_SCOPES",
    ["test-scope1", "test-scope2"],
)
def test_scoped_token_auth():
    token, token_container = gen_token()

    response = APIClient().get("/s/")
    assert response.status_code == 401

    # token is missing scope
    response = APIClient().get(
        "/s/", HTTP_AUTHORIZATION=f"Bearer {token_container.encoded_bearer}"
    )
    assert response.status_code == 403

    token.scopes = "test-scope1"
    token.save()

    # token has scope
    response = APIClient().get(
        "/s/", HTTP_AUTHORIZATION=f"Bearer {token_container.encoded_bearer}"
    )
    assert response.status_code == 200


@pytest.mark.urls(__name__)
@pytest.mark.django_db
def test_token_rehash():
    token, token_container = gen_token()

    assert (
        APIClient()
        .get("/u/", HTTP_AUTHORIZATION=f"Bearer {token_container.encoded_bearer}")
        .status_code
        == 200
    )

    token.refresh_from_db()
    saved_key_original = token.key

    def make_new_password(password) -> str:
        hasher = get_hasher("pbkdf2_sha256")
        return hasher.encode(password, hasher.salt(), iterations=5_000)  # type: ignore

    def check_new_password_rehash(raw_password: str) -> bool:
        return not raw_password.startswith("pbkdf2_sha256$5000$")

    with mock.patch(
        "django_seriously.settings.seriously_settings.CHECK_PASSWORD_REHASH",
        check_new_password_rehash,
    ), mock.patch(
        "django_seriously.settings.seriously_settings.MAKE_PASSWORD", make_new_password
    ):
        assert (
            APIClient()
            .get("/u/", HTTP_AUTHORIZATION=f"Bearer {token_container.encoded_bearer}")
            .status_code
            == 200
        )

        token.refresh_from_db()
        saved_key_rehashed = token.key

        assert (
            APIClient()
            .get("/u/", HTTP_AUTHORIZATION=f"Bearer {token_container.encoded_bearer}")
            .status_code
            == 200
        )

        token.refresh_from_db()
        saved_key_rehashed2 = token.key

    assert saved_key_original.startswith("pbkdf2_sha256$1000$")
    assert saved_key_rehashed.startswith("pbkdf2_sha256$5000$")
    # no change in method, so nothing is supposed to change
    assert saved_key_rehashed == saved_key_rehashed2
