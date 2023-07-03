import base64
import os
import uuid

from django.contrib.auth.hashers import get_hasher

from django_seriously.settings import seriously_settings


class TokenContainer:
    """
    A token is comprised of two random 16 byte strings. Id serves as primary key on
    the token table for fast retrieval, while the second part contains the actual
    secret. The token table will only contain a salted and hashed value for
    comparison (key), while cleartext secret is never persisted.

    bearer = id + secret
    encoded_bearer = base64(bearer)
    key = PBKDF2(secret)
    """

    id: uuid.UUID
    key: str
    bearer: bytes
    encoded_bearer: str

    def __init__(self, id, key, bearer, encoded_bearer):
        self.id = id
        self.key = key
        self.bearer = bearer
        self.encoded_bearer = encoded_bearer


def generate_token() -> TokenContainer:
    token_id = uuid.uuid4()
    secret = os.urandom(16)
    raw_bearer_token = token_id.bytes + secret
    return TokenContainer(
        id=token_id,
        key=seriously_settings.MAKE_PASSWORD(secret),
        bearer=raw_bearer_token,
        encoded_bearer=base64.urlsafe_b64encode(raw_bearer_token).decode(),
    )


def make_password(password) -> str:
    """Default hasher function used by seriously_settings.MAKE_PASSWORD"""
    if not isinstance(password, (bytes, str)):
        raise TypeError(
            f"Password must be a string or bytes, got {type(password).__qualname__}."
        )
    hasher = get_hasher("pbkdf2_sha256")
    return hasher.encode(password, hasher.salt(), iterations=1_000)  # type: ignore


def check_password_rehash(raw_password: str) -> bool:
    return not raw_password.startswith("pbkdf2_sha256$1000$")
