from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from pydantic import TypeAdapter

from django_seriously.pydantic.forms import PydanticJSONFormField, ValidatedJSONFormField
from django_seriously.pydantic.mixin import PydanticMixin


class ValidatedJSONField(PydanticMixin, models.JSONField):
    """
    Model field that validates JSON data structures according to a specified
    pydantic model (structure). Data remains in generic python objects, while
    pydantic is only used for validation on save.
    """

    def __init__(self, structure: Any, **kwargs):
        self.structure = (
            structure if isinstance(structure, TypeAdapter) else TypeAdapter(type=structure)
        )
        kwargs.setdefault("encoder", DjangoJSONEncoder)
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.structure is not None:
            kwargs["structure"] = self.structure
        return name, path, args, kwargs

    def validate(self, value, model_instance):
        # Checks whether value is JSON serializable with given encoder
        super(models.JSONField, self).validate(value, model_instance)
        # In addition, we check whether value actually validates against
        # given pydantic structure model.
        self._loads(value)

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        return super().formfield(
            **{
                "form_class": form_class or ValidatedJSONFormField,
                "structure": self.structure,
                **kwargs,
            }
        )


class PydanticJSONField(ValidatedJSONField):
    """
    Model field that validates JSON data structures according to a specified
    pydantic model (structure). Data will be deserialized to an instance of
    the pydantic model class.
    """

    def validate(self, value, model_instance):
        super(models.JSONField, self).validate(value, model_instance)
        # this is somewhat stupid, but pydantic only validates on load and
        # thus validation errors can only be caught with this extra step.
        self._loads(self._dump_json(value))

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return self._loads(value)

    def to_python(self, value):
        if value is None:
            return value
        return self._loads(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        if isinstance(value, bytes):
            return value
        return self._dump_python(value)

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        return super().formfield(
            **{
                "form_class": form_class or PydanticJSONFormField,
                "structure": self.structure,
                **kwargs,
            }
        )
