================
django-seriously
================

|build-status| |pypi-version|

    *... wait, why isn't this part of Django already?*

A focused collection of `Django`_ and `Django REST framework`_ utilities that solve real,
recurring problems — the kind you keep re-inventing or copy&pasting in every new project.

.. code:: bash

    $ pip install django-seriously


What's in the box
-----------------

- `PydanticJSONField`_ — typed, validated JSON fields backed by Pydantic
- `TokenAuthentication`_ — secure, scoped API tokens without the OAuth2 overhead
- `BaseModel`_ — UUID PKs, timestamps, and guaranteed validation on every save
- `MinimalUser`_ — email-only user model without the cruft
- `AdminItemAction`_ — per-row action buttons in Django admin list views
- `admin_navigation_link`_ — clickable links between related models in admin


Features
--------


.. _PydanticJSONField:

``PydanticJSONField`` / ``ValidatedJSONField``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Django's ``JSONField`` is a black box — anything goes in, no guarantees come out.
These fields bring schema validation and automatic deserialization using Pydantic v2.

- ``PydanticJSONField`` — validates *and* deserializes to a typed Pydantic model instance
- ``ValidatedJSONField`` — validates structure but keeps the raw Python object

.. code:: python

    from pydantic import BaseModel
    from django_seriously.pydantic.fields import PydanticJSONField

    class Address(BaseModel):
        street: str
        city: str
        zip_code: str

    class Contact(models.Model):
        address = PydanticJSONField(structure=Address)

    # Validated and deserialized automatically — no manual parsing needed
    contact = Contact.objects.get(pk=pk)
    print(contact.address.city)  # 'Berlin'

Works seamlessly in:

- Django admin (pretty-printed JSON editor)
- DRF serializers (auto-detected)
- Form validation
- Seamless integration with `drf-spectacular`_. OpenAPI3-compliant schemas for those validated JSON fields.


.. _TokenAuthentication:

``TokenAuthentication``
~~~~~~~~~~~~~~~~~~~~~~~

When dealing with OAuth2 is overkill, DRF's built-in token is just horrible, and
`django-rest-knox`_ just doesn't fit your permissioning model.

**Security:**

- Tokens are never stored in plain text — only a PBKDF2 hash is saved
- Bearer token format: ``base64(uuid + random_secret)`` — UUID for **fast** DB lookup, secret for verification
- Optional: Scopes

**Simple usage** (just authentication, no scopes):

.. code:: python

    from django_seriously.authtoken.authentication import TokenAuthentication

    class ReportsViewSet(viewsets.ModelViewSet):
        authentication_classes = [TokenAuthentication]
        permission_classes = [IsAuthenticated]

**With scope-based permissions:**

.. code:: python

    # settings.py
    SERIOUSLY_SETTINGS = {
        "AUTH_TOKEN_SCOPES": ["read", "write", "admin"]
    }

    # views.py
    from django_seriously.authtoken.authentication import TokenAuthentication, TokenHasScope

    class ReportsViewSet(viewsets.ModelViewSet):
        authentication_classes = [TokenAuthentication]
        permission_classes = [TokenHasScope]
        required_scopes = ['read']

**Admin integration:** tokens are shown once at creation (copy/paste), then stored only as hashes — just like a good secret manager.


.. _BaseModel:

``BaseModel``
~~~~~~~~~~~~~

The abstract base model you define in every new project, done properly.

- **UUID primary key** (``uuid4``) — no sequential ID leakage
- **Automatic timestamps** — immutable ``created_at``, auto-updating ``updated_at``
- **Validation always runs** — overrides ``save()`` to call ``full_clean()`` every time, not just through forms/admin

That last point matters: Django only runs model validation in forms and the admin by default. Direct ``.save()`` calls silently skip your ``clean()`` logic. ``BaseModel`` closes that gap.

.. code:: python

    from django_seriously.utils.models import BaseModel

    class Article(BaseModel):
        title = models.CharField(max_length=200)
        # uuid pk, created_at, updated_at included
        # full_clean() called automatically on every save()


.. _MinimalUser:

``MinimalUser``
~~~~~~~~~~~~~~~

Django's ``AbstractUser`` ships with ``username``, ``first_name``, ``last_name``, and other fields that most modern apps don't need. ``MinimalAbstractUser`` strips that down to what you actually use.

- Email-based authentication (no ``username`` field)
- Supports passwordless user creation (magic links, SSO)
- Drop-in ``MinimalUserAdmin`` included

.. code:: python

    # models.py
    from django_seriously.minimaluser.models import MinimalAbstractUser
    from django_seriously.utils.models import BaseModel

    class User(BaseModel, MinimalAbstractUser):
        # Add your fields here
        pass

    # admin.py
    from django_seriously.minimaluser.admin import MinimalUserAdmin

    @admin.register(User)
    class UserAdmin(MinimalUserAdmin):
        pass


.. _AdminItemAction:

``AdminItemAction``
~~~~~~~~~~~~~~~~~~~

Django admin's built-in actions apply to a selected batch of rows. ``AdminItemAction`` puts a context-aware action button directly on each row — and only shows it when the action makes sense for that item.

.. code:: python

    # admin.py
    from django_seriously.utils.admin import AdminItemAction

    class UserAdminAction(AdminItemAction[User]):
        model_cls = User
        actions = [("reset_invitation", "Reset Invitation")]

        @classmethod
        def is_actionable(cls, obj: User, action: str) -> bool:
            if action == "reset_invitation":
                return obj.invitation_pending
            return False

        def perform_action(self, obj: User, action: str) -> None:
            if action == "reset_invitation":
                send_invitation(obj)  # your code

    @admin.register(User)
    class UserAdmin(ModelAdmin):
        list_display = (..., "admin_actions")

        def admin_actions(self, obj: User):
            return UserAdminAction.action_markup(obj)

.. code:: python

    # urls.py — item actions must precede regular admin endpoints
    urlpatterns = [
        path("admin/", AdminItemAction.urls()),
        path("admin/", admin.site.urls),
    ]


.. _admin_navigation_link:

``admin_navigation_link``
~~~~~~~~~~~~~~~~~~~~~~~~~

Click through from any list view to a related model's change page — one line of code.

.. code:: python

    from django_seriously.utils.admin import admin_navigation_link

    @admin.register(Article)
    class ArticleAdmin(ModelAdmin):
        list_display = ('id', 'title', 'author_link')

        def author_link(self, obj: Article):
            return admin_navigation_link(obj.author, label=obj.author.email)


Demo
----

``AdminItemAction``, ``admin_navigation_link``, ``MinimalUser``, and ``TokenAuthentication`` in action:

.. image:: https://github.com/tfranzel/django-seriously/blob/master/docs/demo.gif


Requirements
------------

- Python >= 3.12
- Django >= 4.2
- Pydantic >= 2.0
- Django REST Framework (optional)


License
-------

Provided by `T. Franzel <https://github.com/tfranzel>`_, `Licensed under 3-Clause BSD <https://github.com/tfranzel/django-seriously/blob/master/LICENSE>`_.


.. _Django: https://www.djangoproject.com/
.. _Django REST framework: https://www.django-rest-framework.org/
.. _django-rest-knox: https://github.com/James1345/django-rest-knox
.. _drf-spectacular: https://github.com/tfranzel/drf-spectacular

.. |pypi-version| image:: https://img.shields.io/pypi/v/django-seriously.svg
   :target: https://pypi.python.org/pypi/django-seriously
.. |build-status| image:: https://github.com/tfranzel/django-seriously/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/tfranzel/django-seriously/actions/workflows/ci.yml