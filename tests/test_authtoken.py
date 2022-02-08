from unittest import mock

import pytest
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


def gen_token():
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
