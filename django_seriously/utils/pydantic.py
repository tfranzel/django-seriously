import json
from typing import Any

from django.core import exceptions
from pydantic import BaseModel, ValidationError, parse_obj_as, parse_raw_as


def _build_container(structure, *, json_loads=None, json_dumps=None):
    loads_callable = json_loads or json.loads
    dumps_callable = json_dumps or json.dumps

    class Tmp(BaseModel):
        __root__: structure  # type: ignore

        class Config:
            json_loads = loads_callable
            json_dumps = dumps_callable

    return Tmp


def _is_pydantic(value: Any) -> bool:
    try:
        return isinstance(value, BaseModel)
    except TypeError:
        return False


def pydantic_dumps(structure, value: Any, *, json_dumps=None, encoder=None) -> str:
    try:
        if _is_pydantic(value) and not json_dumps:
            obj = value
        else:
            obj = _build_container(structure, json_dumps=json_dumps)(__root__=value)
        return obj.json()
    except ValidationError as e:
        raise exceptions.ValidationError(f"Invalid type structure for {structure}: {e}")


def pydantic_loads(structure, value: Any, *, json_loads=None, decoder=None) -> Any:
    try:
        if json_loads:
            # enclose structure in thin wrapper to inject custom json_loads
            structure = _build_container(structure, json_loads=json_loads)
        if isinstance(value, (str, bytes)):
            result = parse_raw_as(structure, value)
        else:
            result = parse_obj_as(structure, value)
        # unpack added wrapper
        return result.__root__ if json_loads else result
    except ValidationError as e:
        raise exceptions.ValidationError(f"Invalid type structure for {structure}: {e}")


class PydanticMixin:
    def _dumps(self, value):
        return pydantic_dumps(
            self.structure, value, json_dumps=self.json_dumps, encoder=self.encoder
        )

    def _loads(self, value):
        return pydantic_loads(
            self.structure, value, json_loads=self.json_loads, decoder=self.decoder
        )
