from typing import TypeVar

from _typeshed import DataclassInstance

DataclassType = TypeVar("DataclassType", bound=DataclassInstance)
