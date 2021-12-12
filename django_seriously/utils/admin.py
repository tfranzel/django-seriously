import abc
from typing import Any, Generic, Optional, Type, TypeVar

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.db import models, transaction
from django.http.response import HttpResponse, JsonResponse
from django.urls.base import reverse
from django.urls.conf import path, include
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

_T = TypeVar("_T", bound=models.Model)


class AdminRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is admin"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)  # type: ignore


class AdminItemAction(AdminRequiredMixin, View, Generic[_T], metaclass=abc.ABCMeta):
    """
    convenience view for having a context sensitive button per item in the admin list view.
    """

    _registry: list[Type["AdminItemAction"]] = []
    model_cls: Type[_T]
    successful_message = _("Action completed successfully")
    error_message = _("Action failed: {}")
    actions = [
        ("nop", _("No operation")),
    ]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)  # type: ignore
        cls._registry.append(cls)

    def post(self, request, id: str, action: str):
        try:
            # try to obtain referenced model object
            obj = self.model_cls.objects.get(id=id)
            # see if object is still actionable (might have changed in the meantime)
            with transaction.atomic():
                if not self.is_actionable(obj, action):
                    raise ValueError("not actionable anymore")
                res = self.perform_action(obj, action)
            messages.success(request, self.successful_message)
            if res is None:
                return HttpResponse(status=204)
            else:
                return JsonResponse(res, safe=False)
        except Exception as e:
            messages.error(request, self.error_message.format(e))
            return HttpResponse(status=400)

    @abc.abstractmethod
    def perform_action(self, obj: _T, action: str) -> Any:
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def is_actionable(cls, obj: _T, action: str) -> bool:
        """does the action apply to this particular object"""
        return True

    @classmethod
    def extra_javascript(cls):
        return ""

    @classmethod
    def action_markup(cls, obj: _T):
        return mark_safe(
            " ".join([cls._action(obj, action, label) for action, label in cls.actions])
        )

    @classmethod
    def _action(cls, obj: _T, action: str, label: str):
        """template rendering of action"""
        if not cls.is_actionable(obj, action):
            return ""

        return format_html(
            """
            <a class="button" href="#" style="white-space: nowrap" onclick="
                if (!confirm('Are you sure performing this action?')) {{
                    return false;
                }}
                fetch('{}', {{
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {{
                        'X-CSRFTOKEN': document.querySelector('#changelist-form > input[type=hidden]').value
                    }}
                }})
                .then(async (resp) => {{
                    {}
                    location.reload(true);
                }})
                .catch(err => alert('request failed. please try again.'));
                return false;">{}</a>
            """,  # noqa: E501
            reverse(cls.__name__.lower(), args=[obj.pk, action]),
            cls.extra_javascript(),
            label,
        )

    @classmethod
    def _path(cls):
        """returns a urlpattern for registration in settings"""
        return path(
            route=(
                f"{cls.model_cls._meta.app_label}/{cls.model_cls.__name__.lower()}/"
                f"<uuid:id>/{cls.__name__.lower()}/<str:action>/"
            ),
            view=cls.as_view(),
            name=cls.__name__.lower(),
        )

    @classmethod
    def urls(cls):
        return include([item._path() for item in cls._registry])


def admin_navigation_link(
    entity: Type[models.Model], label: Optional[str] = None
) -> str:
    if not entity:
        return ""

    url = reverse(
        f"admin:{entity._meta.app_label}_{entity._meta.model_name}_change",
        args=[entity.pk],
    )
    if not label:
        label = str(entity)
    return format_html(f'<a href="{url}">{label}</a>')
