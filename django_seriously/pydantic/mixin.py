from typing import Any

from django.core import exceptions
from pydantic import BaseModel, TypeAdapter, ValidationError


class PydanticMixin:
    structure: TypeAdapter

    def _dump_json(self, value: Any, indent: int | None = None) -> bytes:
        try:
            return self.structure.dump_json(value, indent=indent)
        except ValidationError as e:
            raise exceptions.ValidationError(
                f"Invalid type structure for {self.structure._type.__name__}: {e}"
            )

    def _dump_python(self, value: Any) -> dict[str, Any]:
        try:
            return self.structure.dump_python(value)
        except ValidationError as e:
            raise exceptions.ValidationError(
                f"Invalid type structure for {self.structure._type.__name__}: {e}"
            )

    def _loads(self, value: Any) -> BaseModel:
        try:
            if isinstance(value, (str, bytes)):
                return self.structure.validate_json(value)
            else:
                return self.structure.validate_python(value)
        except ValidationError as e:
            raise exceptions.ValidationError(
                f"Invalid type structure for {self.structure._type.__name__}: {e}"
            )
