from datetime import datetime

import pytest
from django.core import exceptions
from django.utils import timezone
from pydantic import BaseModel as PydanticBaseModel

from django_seriously.utils.fields import ValidatedJSONField
from django_seriously.utils.models import BaseModel


class X(PydanticBaseModel):
    a: int
    b: str
    c: datetime


class ValidatedFieldTestModel(BaseModel):
    field = ValidatedJSONField(structure=X)
    field_list = ValidatedJSONField(structure=list[X])


X_EXAMPLE_DICT = {"a": 1, "b": "foo", "c": timezone.now()}


@pytest.mark.django_db
def test_validated_field():
    instance = ValidatedFieldTestModel.objects.create(
        field=X_EXAMPLE_DICT, field_list=[X_EXAMPLE_DICT]
    )
    assert isinstance(instance.field, dict)
    assert instance.field == X_EXAMPLE_DICT
    assert instance.field_list[0] == X_EXAMPLE_DICT


@pytest.mark.django_db
def test_validated_field_validation():
    with pytest.raises(exceptions.ValidationError):
        ValidatedFieldTestModel.objects.create(field=1, field_list=[X_EXAMPLE_DICT])
    with pytest.raises(exceptions.ValidationError):
        ValidatedFieldTestModel.objects.create(field=X_EXAMPLE_DICT, field_list=[1])
