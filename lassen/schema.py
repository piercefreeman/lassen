from typing import Generic, TypeVar

from pydantic.generics import GenericModel

T = TypeVar("T")


class SearchWrapper(GenericModel, Generic[T]):
    count: int
    limit: int
    skip: int
    items: list[T]
