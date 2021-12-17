from datetime import datetime

import pytest
from django.core import exceptions
from django.utils import timezone
from pydantic import BaseModel as PydanticBaseModel

from django_seriously.utils.fields import PydanticJSONField
from django_seriously.utils.models import BaseModel


class X(PydanticBaseModel):
    a: int
    b: str
    c: datetime


class PydanticFieldTestModel(BaseModel):
    field = PydanticJSONField(structure=X)
    field_list = PydanticJSONField(structure=list[X])


X_EXAMPLE_DICT = {"a": 1, "b": "foo", "c": timezone.now()}


@pytest.mark.parametrize("field_input", [X_EXAMPLE_DICT, X(**X_EXAMPLE_DICT)])
@pytest.mark.django_db
def test_pydantic_field_creation(field_input):
    instance = PydanticFieldTestModel.objects.create(
        field=field_input,
        field_list=[field_input],
    )
    assert isinstance(instance.field, X)
    assert isinstance(instance.field_list[0], X)
    instance_retrieved = PydanticFieldTestModel.objects.get()
    assert isinstance(instance_retrieved.field, X)
    assert isinstance(instance_retrieved.field_list[0], X)


@pytest.mark.django_db
def test_pydantic_field_invalid_creation():
    with pytest.raises(exceptions.ValidationError):
        PydanticFieldTestModel.objects.create(field=1, field_list=[X_EXAMPLE_DICT])
    with pytest.raises(exceptions.ValidationError):
        PydanticFieldTestModel.objects.create(field=X_EXAMPLE_DICT, field_list=[1])


@pytest.mark.django_db
def test_pydantic_field_invalid_modification():
    instance = PydanticFieldTestModel.objects.create(
        field=X_EXAMPLE_DICT, field_list=[X_EXAMPLE_DICT]
    )

    instance.field.a = 2
    instance.save()

    instance.field.a = "NaN"
    with pytest.raises(exceptions.ValidationError):
        instance.save()

    # previous validation should make this never fail
    instance.refresh_from_db()

    instance.field_list = [{"invalid": "invalid"}]
    with pytest.raises(exceptions.ValidationError):
        instance.save()
