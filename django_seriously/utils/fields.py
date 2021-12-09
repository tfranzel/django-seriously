import pydantic
from django.core import exceptions
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class ValidatedJSONField(models.JSONField):
    """
    Model field that validates json data structure according to specified
    pydantic model. Data remains in generic python objects, while pydantic
    is only used for validation on save.
    """

    def __init__(self, type, **kwargs):
        self._type = type
        kwargs.setdefault("encoder", DjangoJSONEncoder)
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["type"] = None
        return name, path, args, kwargs

    def validate(self, value, model_instance):
        super(models.JSONField, self).validate(value, model_instance)
        try:
            if isinstance(value, (str, bytes)):
                pydantic.parse_raw_as(self._type, value)
            else:
                pydantic.parse_obj_as(self._type, value)
        except pydantic.ValidationError as e:
            raise exceptions.ValidationError(
                f"Invalid type structure structure for {self._type}: {e}",
            )
