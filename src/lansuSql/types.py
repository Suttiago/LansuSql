from typing import TypeVar, Any, Dict, Union
from uuid import UUID

ModelType = TypeVar("ModelType", bound=Any)

PrimaryKeyType = Union[int, str, UUID]

UpdateDict = Dict[str, Any]

FilterDict = Dict[str, Any]

__all__ = [
    "ModelType",
    "PrimaryKeyType",
    "UpdateDict",
    "FilterDict"
]