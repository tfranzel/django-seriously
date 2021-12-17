from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from django_seriously.utils.forms import PydanticJSONFormField
from django_seriously.utils.pydantic import PydanticMixin


class ValidatedJSONField(PydanticMixin, models.JSONField):
    """
    Model field that validates json data structure according to specified
    pydantic model. Data remains in generic python objects, while pydantic
    is only used for validation on save.
    """

    def __init__(self, structure, **kwargs):
        self.structure = structure
        if structure in [str, bytes]:
            raise ValueError("ValidatedJSONField requires non-trivial structure")
        kwargs.setdefault("encoder", DjangoJSONEncoder)
        self.json_loads = kwargs.pop("json_loads", None)
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["structure"] = None
        return name, path, args, kwargs

    def validate(self, value, model_instance):
        super(models.JSONField, self).validate(value, model_instance)
        self._loads(value)


class PydanticJSONField(PydanticMixin, models.JSONField):
    """ """

    def __init__(self, structure, **kwargs):
        self.structure = structure
        if structure in [str, bytes]:
            raise ValueError("PydanticJSONField requires non-trivial structure")
        kwargs.setdefault("encoder", DjangoJSONEncoder)
        self.json_loads = kwargs.pop("json_loads", None)
        self.json_dumps = kwargs.pop("json_dumps", None)
        self._initial = None
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["structure"] = None
        return name, path, args, kwargs

    def validate(self, value, model_instance):
        super(models.JSONField, self).validate(value, model_instance)
        # this is somewhat stupid, but pydantic only validates on load and
        # thus validation errors can only be caught with this extra step.
        # try to be a bit smarter by skipping loading when nothing changed
        dumped_value = self._dumps(value)
        if dumped_value != self._initial:
            self._loads(dumped_value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        self._initial = value
        return self._loads(value)

    def to_python(self, value):
        if value is None:
            return value
        return self._loads(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        return self._dumps(value)

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": PydanticJSONFormField,
                "structure": self.structure,
                "encoder": self.encoder,
                "decoder": self.decoder,
                "json_loads": self.json_loads,
                "json_dumps": self.json_dumps,
                **kwargs,
            }
        )
