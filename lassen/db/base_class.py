from typing import Any

from inflection import underscore
from sqlalchemy import Boolean, Column, event, false
from sqlalchemy.orm import (
    Mapped,
    Session,
    declarative_base,
    declarative_mixin,
    declared_attr,
    with_loader_criteria,
)


@declarative_mixin
class MainMixin:
    id: Any
    __name__: str

    # Generate __tablename__ automatically
    # Quirk of python's type system that cls MainMixin here (an instance) instead of Type[MainMixin] (a class)
    @declared_attr
    def __tablename__(cls: "MainMixin") -> Mapped[str]:
        return underscore(cls.__name__)  # type: ignore


class ArchivedMixin:
    archived = Column(Boolean, default=False, nullable=False)


Base = declarative_base()


# https://docs.sqlalchemy.org/en/14/_modules/examples/extending_query/filter_public.html
@event.listens_for(Session, "do_orm_execute")
def _add_filtering_criteria(execute_state):
    """Intercept all ORM queries.   Add a with_loader_criteria option to all
    of them.

    This option applies to SELECT queries and adds a global WHERE criteria
    (or as appropriate ON CLAUSE criteria for join targets)
    to all objects of a certain class or superclass.

    """

    # the with_loader_criteria automatically applies itself to
    # relationship loads as well including lazy loads.   So if this is
    # a relationship load, assume the option was set up from the top level
    # query.

    if (
        not execute_state.is_column_load
        and not execute_state.is_relationship_load
        and not execute_state.execution_options.get("include_archived", False)
    ):
        # Default behavior will filter out archived items
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                ArchivedMixin,
                lambda cls: cls.archived == false(),
                include_aliases=True,
            )
        )
