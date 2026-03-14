from django.core.exceptions import ValidationError
from django.forms import JSONField
from django.forms.fields import CharField, InvalidJSONInput, JSONString

from django_seriously.pydantic.mixin import PydanticMixin


class ValidatedJSONFormField(PydanticMixin, JSONField):
    def __init__(self, structure, **kwargs):
        self.structure = structure
        super().__init__(**kwargs)

    def prepare_value(self, value):
        if isinstance(value, InvalidJSONInput):
            return value
        return self._dump_json(value, indent=2).decode()


class PydanticJSONFormField(ValidatedJSONFormField):
    def to_python(self, value):
        if self.disabled:
            return value
        if value in self.empty_values:
            return None
        elif isinstance(value, (list, dict, int, float, JSONString)):
            return value
        try:
            converted = self._loads(value)
        except ValidationError as e:
            raise ValidationError(
                e.message,
                code="invalid",
                params={"value": value},
            )
        if isinstance(converted, str):
            return JSONString(converted)
        else:
            return converted

    def bound_data(self, data, initial):
        if self.disabled:
            return initial
        if data is None:
            return None
        try:
            return self._loads(data)
        except ValidationError:
            return InvalidJSONInput(data)

    def has_changed(self, initial, data):
        if CharField.has_changed(self, initial, data):
            return True
        # For purposes of seeing whether something has changed, True isn't the
        # same as 1 and the order of keys doesn't matter.
        return self._dump_json(initial) != self._dump_json(self.to_python(data))
