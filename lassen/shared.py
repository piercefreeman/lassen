from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

    DataclassType = TypeVar("DataclassType", bound=DataclassInstance)
else:
    DataclassType = TypeVar("DataclassType")
