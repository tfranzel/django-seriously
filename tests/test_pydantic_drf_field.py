import pytest
from django.db import models
from django.urls import include, path
from pydantic import BaseModel
from rest_framework import routers, serializers, viewsets
from rest_framework.test import APIClient

from django_seriously.pydantic.model_fields import PydanticJSONField, ValidatedJSONField


class PydanticNestedExample(BaseModel):
    fpn: float


class PydanticExample(BaseModel):
    number: int
    text: str
    nested: PydanticNestedExample


class ExampleModel(models.Model):
    val = ValidatedJSONField(structure=PydanticExample, null=True, blank=True)
    pyd = PydanticJSONField(structure=PydanticExample)


class ExampleSerializer(serializers.ModelSerializer):
    """make sure auto-generated serializer fields works"""

    class Meta:
        model = ExampleModel
        fields = "__all__"


class ExampleViewSet(viewsets.ModelViewSet):
    queryset = ExampleModel.objects.all()
    serializer_class = ExampleSerializer


router = routers.SimpleRouter()
router.register("api/example", ExampleViewSet)
urlpatterns = [path("", include(router.urls))]


@pytest.mark.django_db
@pytest.mark.urls(__name__)
def test_spectacular_view(no_warnings):
    response = APIClient().post(
        "/api/example/",
        data={"pyd": {"number": 3, "text": "asdasd", "nested": {"fpn": 3.3}}},
        format="json",
    )
    assert response.status_code == 201, response.content

    obj = ExampleModel.objects.get()
    assert obj


@pytest.mark.django_db
@pytest.mark.urls(__name__)
def test_spectacular_view2(no_warnings):
    response = APIClient().post(
        "/api/example/",
        data={"pyd": {"number": "asd"}},
        format="json",
    )
    assert response.status_code == 400, response.content
