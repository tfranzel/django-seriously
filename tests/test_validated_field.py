from datetime import datetime

import pytest
from django.core import exceptions
from django.utils import timezone
from pydantic import BaseModel as PydanticBaseModel

from django_seriously.pydantic.model_fields import ValidatedJSONField
from django_seriously.utils.models import DjangoBaseModel


class X(PydanticBaseModel):
    a: int
    b: str
    c: datetime


class ValidatedFieldTestModel(DjangoBaseModel):
    # direct usage of BaseModel
    field = ValidatedJSONField(structure=X)
    # indirect usage of a model that is implicitly wrapped in TypeAdapter
    field_list = ValidatedJSONField(structure=list[X])


def get_x_instance():
    return {
        "a": 1,
        "b": "foo",
        "c": datetime.fromisoformat("2025-03-02T20:08:25.000Z"),
    }


@pytest.mark.django_db
def test_validated_field_creation():
    instance = ValidatedFieldTestModel.objects.create(
        field=get_x_instance(),
        field_list=[get_x_instance()],
    )
    assert isinstance(instance.field, dict)
    assert instance.field == get_x_instance()
    assert instance.field_list == [get_x_instance()]


@pytest.mark.django_db
def test_validated_field_validation_creation_fail():
    with pytest.raises(exceptions.ValidationError):
        ValidatedFieldTestModel.objects.create(field=1, field_list=[get_x_instance()])
    with pytest.raises(exceptions.ValidationError):
        ValidatedFieldTestModel.objects.create(field=get_x_instance(), field_list=[1])
    with pytest.raises(exceptions.ValidationError):
        ValidatedFieldTestModel.objects.create(
            field={"a": "WRONG TYPE", "b": "foo", "c": timezone.now()},
            field_list=[get_x_instance()],
        )


@pytest.mark.django_db
def test_validated_field_update():
    instance = ValidatedFieldTestModel.objects.create(
        field=get_x_instance(),
        field_list=[get_x_instance()],
    )

    instance.field["a"] = 3
    instance.save()

    with pytest.raises(exceptions.ValidationError):
        instance.field["a"] = "invalid value"
        instance.save()


@pytest.mark.django_db
def test_validated_field_retrieval():
    instance = ValidatedFieldTestModel.objects.create(
        field=get_x_instance(),
        field_list=[get_x_instance()],
    )

    instance_retrieved = ValidatedFieldTestModel.objects.get()

    assert isinstance(instance_retrieved.field, dict)
    assert instance.field["a"] == instance_retrieved.field["a"]
    assert instance.field["b"] == instance_retrieved.field["b"]
    # datetime is retrieved as str from the DB
    assert instance.field["c"] == datetime.fromisoformat(instance_retrieved.field["c"])
