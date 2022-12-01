from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import follow_field_source


class PydanticJsonFieldExtensions(OpenApiSerializerFieldExtension):
    """
    extension class for drf-spectacular that hooks into JSONField
    parsing and injects `structure`'s schema instead of using a
    catch-all object.
    Simply import this file into your project to load the extension
    """

    target_class = "rest_framework.fields.JSONField"

    def map_serializer_field(self, auto_schema, direction):
        if hasattr(self.target.parent, "Meta"):
            model = self.target.parent.Meta.model
            source = self.target.source.split(".")
            model_field = follow_field_source(model, source)

            if hasattr(model_field, "structure"):
                # let pydantic generate as JSON Schema
                return model_field.structure.schema()

        return auto_schema._map_serializer_field(
            self.target, direction, bypass_extensions=True
        )
