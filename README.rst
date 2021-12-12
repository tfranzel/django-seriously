================
django-seriously
================

|pypi-version|

    ... wait what? no seriously, why isn't that part of Django/DRF?

Opinionated collection of `Django`_ and `Django REST framework`_ tools that came in handy time and again.

- ``AdminItemAction``
    - Allow triggering context-aware custom admin operations in model list views.

- ``admin_navigation_link``
    - Allow navigation from the admin list view to other related models via links.

- ``MinimalUser`` (abstract model)
    - Bare minimum user model ready for customization.
    - Removes the username and auxiliary fields like ``first_name`` and ``last_name``.
    - Allow creating users without a valid password (unusable password)
    - Abstract since its highly recommended to subclass the user model anyway.

- ``ValidatedJSONField`` (model field)
    - validate the structure of JSON fields with Pydantic models.

- ``TokenAuthentication``
    - When OAuth2 adds too much complexity, DRF's TokenAuthentication is too simple, and
      `django-rest-knox`_ does not quite fit the permissioning.
    - No plain passwords in database (PBKDF2, i.e. hashed and salted)
    - Enabled for permission scoping
    - Easy (one-time-view) token creation in Django admin

- ``BaseModel`` (abstract model)
    - Reusable base model with automatic ``created_at``, ``updated_at`` fields.
    - Primary key is a random UUID (``uuid4``).
    - Ensure validation logic (``full_clean()``) always runs, not just in a subset of cases.

- ``AppSettings``
    - A settings container with defaults and string importing inspired by DRF's ``APISettings``


License
-------

Provided by `T. Franzel <https://github.com/tfranzel>`_, `Licensed under 3-Clause BSD <https://github.com/tfranzel/django-seriously/blob/master/LICENSE>`_.

Requirements
------------

-  Python >= 3.6
-  Django >= 3.0
-  Django REST Framework (optional)

Installation
------------

.. code:: bash

    $ pip install django-seriously


Usage
-----

``AdminItemAction``
^^^^^^^^^^^^^^^^^^^

.. code:: python

    # admin.py
    from django_seriously.utils.admin import AdminItemAction


    class UserAdminAction(AdminItemAction[User]):
        model_cls = User
        actions = [
            ("reset_invitation", "Reset Invitation"),
        ]

        @classmethod
        def is_actionable(cls, obj: User, action: str) -> bool:
            # check whether action should be shown for this item
            if action == "reset_invitation":
                return is_user_resettable_check(obj) # your code
            return False

        def perform_action(self, obj: User, action: str) -> Any:
            # perform the action on the item
            if action == "reset_invitation":
                perform_your_resetting(obj)  # your code
                obj.save()


    @admin.register(User)
    class UserAdmin(ModelAdmin):
        # insert item actions into a list view column
        list_display = (..., "admin_actions")

        def admin_actions(self, obj: User):
            return UserAdminAction.action_markup(obj)

.. code:: python

    # urls.py
    from django_seriously.utils.admin import AdminItemAction

    urlpatterns = [
        ...
        # item actions must precede regular admin endpoints
        path("admin/", include(AdminItemAction.paths())),
        path("admin/", admin.site.urls),
    ]


.. _Django: https://www.djangoproject.com/
.. _Django REST framework: https://www.django-rest-framework.org/
.. _django-rest-knox: https://github.com/James1345/django-rest-knox

.. |pypi-version| image:: https://img.shields.io/pypi/v/django-seriously.svg
   :target: https://pypi.python.org/pypi/django-seriously