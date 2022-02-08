import os

import django
import pytest
from django.core import management


def pytest_configure(config):
    from django.conf import settings

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        },
        SITE_ID=1,
        SECRET_KEY="not very secret in tests",
        USE_I18N=True,
        LANGUAGES=[
            ("de-de", "German"),
            ("en-us", "English"),
        ],
        LOCALE_PATHS=[base_dir + "/locale/"],
        STATIC_URL="/static/",
        ROOT_URLCONF="tests.urls",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.debug",
                    ],
                },
            },
        ],
        MIDDLEWARE=(
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.middleware.locale.LocaleMiddleware",
        ),
        INSTALLED_APPS=(
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.sites",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "rest_framework",
            "django_seriously.authtoken",
            "tests",
        ),
        PASSWORD_HASHERS=(
            "django.contrib.auth.hashers.SHA1PasswordHasher",
            "django.contrib.auth.hashers.PBKDF2PasswordHasher",
            "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
            "django.contrib.auth.hashers.BCryptPasswordHasher",
            "django.contrib.auth.hashers.MD5PasswordHasher",
            "django.contrib.auth.hashers.CryptPasswordHasher",
        ),
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        SILENCED_SYSTEM_CHECKS=[
            "rest_framework.W001",
            "fields.E210",
            "security.W001",
            "security.W002",
            "security.W003",
            "security.W009",
            "security.W012",
        ],
    )

    django.setup()
    # For whatever reason this works locally without an issue.
    # on TravisCI content_type table is missing in the sqlite db as
    # if no migration ran, but then why does it work locally?!
    management.call_command("migrate")


@pytest.fixture()
def no_warnings(capsys):
    """make sure test emits no warnings"""
    yield capsys
    captured = capsys.readouterr()
    assert not captured.out
    assert not captured.err
