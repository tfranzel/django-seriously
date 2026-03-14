from datetime import datetime
from typing import Any

import pydantic
import pytest
from django.core import exceptions
from django.utils import timezone
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict

from django_seriously.pydantic.model_fields import PydanticJSONField
from django_seriously.utils.models import DjangoBaseModel


class X(PydanticBaseModel):
    a: int
    b: str
    c: datetime
    d: list[int]


class XStrict(X):
    model_config = ConfigDict(validate_assignment=True)
    a: int
    b: str
    c: datetime
    d: list[int]


class PydanticFieldTestModel(DjangoBaseModel):
    field = PydanticJSONField(structure=X)
    field_list = PydanticJSONField(structure=list[X])


def get_x_instance():
    return {
        "a": 1,
        "b": "foo",
        "c": datetime.fromisoformat("2025-03-02T20:08:25.000Z"),
        "d": [1, 2, 3],
    }


@pytest.mark.parametrize(
    "field_input",
    [
        # test with plain python type as input
        get_x_instance(),  # type: ignore
        # test with pydantic model as input
        X(**get_x_instance()),  # type: ignore
    ],
)
@pytest.mark.django_db
def test_pydantic_field_creation(field_input: Any):
    instance = PydanticFieldTestModel.objects.create(
        field=field_input,
        field_list=[field_input],
    )
    # make sure we end up with a pydantic model regardless of input
    # this case deals with the aftermath of create()
    assert isinstance(instance.field, X)
    assert isinstance(instance.field_list, list)
    assert isinstance(instance.field_list[0], X)

    # recheck if this assumption also holds when we retrieve from DB
    instance_retrieved = PydanticFieldTestModel.objects.get()
    assert isinstance(instance_retrieved.field, X)
    assert isinstance(instance_retrieved.field_list, list)
    assert isinstance(instance_retrieved.field_list[0], X)

    # modifying model and saving it should also work without issue
    instance.field.a = 333
    instance.field_list[0].a = 333
    instance.save()


@pytest.mark.django_db
def test_pydantic_field_invalid_creation():
    with pytest.raises(exceptions.ValidationError):
        PydanticFieldTestModel.objects.create(field=1, field_list=[get_x_instance()])
    with pytest.raises(exceptions.ValidationError):
        PydanticFieldTestModel.objects.create(field=get_x_instance(), field_list=[1])
    with pytest.raises(exceptions.ValidationError):
        PydanticFieldTestModel.objects.create(
            field={"a": "WRONG TYPE", "b": "foo", "c": timezone.now()},
            field_list=[get_x_instance()],
        )


@pytest.mark.django_db
def test_pydantic_field_invalid_modification():
    instance = PydanticFieldTestModel.objects.create(
        field=get_x_instance(),
        field_list=[get_x_instance()],
    )

    instance.field.a = 2
    instance.field_list[0].a = 2
    instance.save()

    instance.field.a = "NaN"
    with pytest.raises(exceptions.ValidationError):
        instance.save()

    # previous validation should make this never fail
    instance.refresh_from_db()

    instance.field_list = [{"invalid": "invalid"}]
    with pytest.raises(exceptions.ValidationError):
        instance.save()


def test_pydantic_assumptions():
    x = X(**get_x_instance())
    x.a = "wrong type"  # type: ignore

    # unfortunately this does not throw
    X.model_validate(x)

    # this however does (as expected), but is more expensive
    with pytest.raises(Exception):
        X.model_validate(x.model_dump())

    # Models with validate_assignment=True do not allow incorrect assignments
    with pytest.raises(pydantic.ValidationError):
        xs = XStrict(**get_x_instance())
        xs.a = "wrong type"  # type: ignore
    with pytest.raises(pydantic.ValidationError):
        xs = XStrict(**get_x_instance())
        xs.d = ["1,2"]  # type: ignore
