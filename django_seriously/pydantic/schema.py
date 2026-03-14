from drf_spectacular.drainage import error
from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import (
    _get_type_hint_origin,
    build_array_type,
    build_basic_type,
    is_higher_order_type_hint,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework.utils.serializer_helpers import ReturnList


class PydanticJsonFieldExtension(OpenApiSerializerFieldExtension):
    """
    Allows using pydantic models on @extend_schema(request=..., response=...) to
    describe your API.

    We only have partial support for pydantic's version of dataclass, due to the way they
    are designed. The outermost class (the @extend_schema argument) has to be a subclass
    of pydantic.BaseModel. Inside this outermost BaseModel, any combination of dataclass
    and BaseModel can be used.
    """

    target_class = "django_seriously.pydantic.drf_fields.ValidatedJSONField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        if not self.target.structure:
            error("Could not find structure attribute containg model on ValidatedJSONField")
            return build_basic_type(OpenApiTypes.ANY)

        is_list = False
        structure = self.target.structure._type

        if is_higher_order_type_hint(structure):
            origin, args = _get_type_hint_origin(structure)
            if origin is list or structure is list or structure is ReturnList:
                is_list, structure = True, args[0]

        schema = auto_schema._map_serializer_field(structure, direction)
        return build_array_type(schema) if is_list else schema
