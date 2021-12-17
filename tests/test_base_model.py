import pytest
from django.core import exceptions
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from django_seriously.utils.models import BaseModel


class TestModel(BaseModel):
    field = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )


@pytest.mark.django_db
def test_base_model_derivation():
    inst = TestModel.objects.create(field=1)
    assert inst.created_at
    assert inst.updated_at
    assert inst.field == 1


@pytest.mark.django_db
def test_base_model_clean_check():
    """forced full_clean makes this raise. otherwise validation would not run"""
    with pytest.raises(exceptions.ValidationError):
        TestModel.objects.create(field=102)
