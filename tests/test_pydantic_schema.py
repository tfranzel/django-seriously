from datetime import datetime

import pytest
from django.db import models
from drf_spectacular.generators import SchemaGenerator
from pydantic import BaseModel
from rest_framework import serializers, viewsets
from rest_framework.routers import SimpleRouter

from django_seriously.pydantic.model_fields import PydanticJSONField, ValidatedJSONField


class Foo(BaseModel):
    """Some pydantic model"""

    a: int
    b: str
    c: datetime


class XModel(models.Model):
    field_plain = models.JSONField(help_text="URL identifier for Aux")
    field_validated = ValidatedJSONField(structure=Foo)
    field_pydantic = PydanticJSONField(structure=Foo)
    field_pydantic_list = PydanticJSONField(structure=list[Foo])


class XSerializer(serializers.ModelSerializer):
    """description for the x object"""

    class Meta:
        fields = "__all__"
        model = XModel


class XModelViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = XSerializer
    queryset = XModel.objects.all()


router = SimpleRouter()
router.register("test", XModelViewset)
urlpatterns = router.urls


@pytest.mark.urls(__name__)
@pytest.mark.django_db
def test_schema(no_warnings):
    generator = SchemaGenerator()
    schema = generator.get_schema(request=None, public=True)

    assert schema["components"]["schemas"] == {
        "Foo": {
            "description": "Some pydantic model",
            "properties": {
                "a": {"title": "A", "type": "integer"},
                "b": {"title": "B", "type": "string"},
                "c": {"format": "date-time", "title": "C", "type": "string"},
            },
            "required": ["a", "b", "c"],
            "title": "Foo",
            "type": "object",
        },
        "X": {
            "type": "object",
            "description": "description for the x object",
            "properties": {
                "id": {"type": "integer", "readOnly": True},
                "field_plain": {"description": "URL identifier for Aux"},
                "field_validated": {"$ref": "#/components/schemas/Foo"},
                "field_pydantic": {"$ref": "#/components/schemas/Foo"},
                "field_pydantic_list": {
                    "items": {"$ref": "#/components/schemas/Foo"},
                    "type": "array",
                },
            },
            "required": [
                "field_plain",
                "field_pydantic",
                "field_pydantic_list",
                "field_validated",
                "id",
            ],
        },
    }
