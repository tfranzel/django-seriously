from django.core import exceptions
from rest_framework.fields import JSONField
from rest_framework.serializers import ModelSerializer

from django_seriously.pydantic.mixin import PydanticMixin
from django_seriously.pydantic.model_fields import PydanticJSONField as PydanticJSONModelField
from django_seriously.pydantic.model_fields import ValidatedJSONField as ValidatedJSONModelField


class ValidatedJSONField(PydanticMixin, JSONField):
    def __init__(self, **kwargs):
        self.structure = kwargs.pop("structure", None)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return self._loads(data)
        except exceptions.ValidationError:
            self.fail("invalid")

    def to_representation(self, value):
        return self._dump_python(value)


def patch_drf_model_serializer():
    """
    since there is no official way to extend DRF model->serializer field translation,
    we need to monkey-patch in the extra kwarg to hand over the structure parameter
    """
    # register mapping
    ModelSerializer.serializer_field_mapping[ValidatedJSONModelField] = ValidatedJSONField
    ModelSerializer.serializer_field_mapping[PydanticJSONModelField] = ValidatedJSONField

    ModelSerializer._build_standard_field = ModelSerializer.build_standard_field  # type: ignore[attr-defined]

    def build_standard_field(self, field_name, model_field):
        # simulate as if we called super() for default behavior
        field_class, field_kwargs = self._build_standard_field(field_name, model_field)
        # and then attach extra kwargs for our custom fields
        if isinstance(model_field, PydanticMixin):
            field_kwargs["structure"] = model_field.structure
        return field_class, field_kwargs

    ModelSerializer.build_standard_field = build_standard_field  # type: ignore[method-assign]


patch_drf_model_serializer()
