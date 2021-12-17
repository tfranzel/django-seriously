from django.core.exceptions import ValidationError
from django.forms import JSONField
from django.forms.fields import InvalidJSONInput, JSONString

from django_seriously.utils.pydantic import PydanticMixin


class PydanticJSONFormField(PydanticMixin, JSONField):
    def __init__(
        self,
        structure,
        encoder=None,
        decoder=None,
        json_loads=None,
        json_dumps=None,
        **kwargs,
    ):
        self.structure = structure
        self.json_loads = json_loads
        self.json_dumps = json_dumps
        super().__init__(encoder=encoder, decoder=decoder, **kwargs)

    def to_python(self, value):
        if self.disabled:
            return value
        if value in self.empty_values:
            return None
        elif isinstance(value, (list, dict, int, float, JSONString)):
            return value
        try:
            converted = self._loads(value)
        except ValidationError:
            raise ValidationError(
                self.error_messages["invalid"],
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

    def prepare_value(self, value):
        if isinstance(value, InvalidJSONInput):
            return value
        return self._dumps(value)

    def has_changed(self, initial, data):
        if super().has_changed(initial, data):
            return True
        # For purposes of seeing whether something has changed, True isn't the
        # same as 1 and the order of keys doesn't matter.
        return self._dumps(initial) != self._dumps(self.to_python(data))
