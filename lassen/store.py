import types
from inspect import isclass
from typing import Any, Generic, Type, TypeVar, get_args, get_type_hints

from pydantic import BaseModel
from sqlalchemy import Column, Table
from sqlalchemy.orm import Query, Session

from lassen.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
FilterSchemaType = TypeVar("FilterSchemaType", bound=BaseModel)


class StoreGlobal(Generic[ModelType]):
    model: Type[ModelType]
    relationship_attributes: dict[str, Type[Base]] = {}

    def __init__(self, model: Type[ModelType]):
        """
        :param `model`: A SQLAlchemy model class
        """
        self.model = model

        # Mapping of relationships to their SQLAlchemy models
        self.relationship_attributes = {
            key: relationship.mapper.class_
            for key, relationship in model.__mapper__.relationships.items()
        }

    def _order_by(self, query: Query):
        # By default, no-op
        return query


class StoreBase(
    Generic[ModelType, CreateSchemaType, UpdateSchemaType], StoreGlobal[ModelType]
):
    def get(self, db: Session, id: Any) -> ModelType | None:
        return db.query(self.model).filter(getattr(self.model, "id") == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int | None = None
    ) -> list[ModelType]:
        query = db.query(self.model)
        query = self._order_by(query)

        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        # obj_in_data = jsonable_encoder(obj_in)
        obj_in_data = obj_in.dict(exclude_unset=True)
        obj_in_data = self.create_dependencies(db, obj_in_data, obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        model_table: Table = getattr(self.model, "__table__")
        model_columns = model_table.columns

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        update_data = self.create_dependencies(db, update_data, obj_in)
        for field, value in update_data.items():
            if field not in model_columns and field not in self.relationship_attributes:
                raise ValueError(f"Model `{self.model}` has no column `{field}`")
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType | None:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj or None

    def create_dependencies(
        self, db: Session, obj_in_data: dict[str, Any], obj_in: Any
    ):
        """
        Creates nested objects that are contained within the primary. Note that this function
        only creates one-depth of dependencies. If you have a dependency that has a dependency,
        you will need to create that dependency separately.

        """
        # Iterate over the dependent relationships and attempt to create these first
        for relationship, relationship_class in self.relationship_attributes.items():
            if relationship not in obj_in_data:
                continue

            static_value = obj_in_data[relationship]
            static_value_original = (
                obj_in[relationship]
                if isinstance(obj_in, dict)
                else getattr(obj_in, relationship)
            )
            database_value = None

            # Determine if we should create a list
            # Otherwise assume this is an object
            if isinstance(static_value, list):
                database_value = []
                for value, original_value in zip(static_value, static_value_original):
                    # print("ORIGINAL", original_value)
                    # If this is a dict, we should cast it otherwise assume it's a SQLAlchemy object
                    if isinstance(original_value, Base):
                        database_value.append(value)
                    else:
                        database_object = relationship_class(**value)
                        # db.add(database_object)
                        # db.commit()
                        # db.refresh(database_object)
                        database_value.append(database_object)

                obj_in_data[relationship] = database_value
            else:
                # If this is a dict, we should cast it otherwise assume it's a SQLAlchemy object
                if isinstance(value, dict):
                    # Create the relationship object
                    database_value = relationship_class(**static_value)
                    # db.add(database_value)
                    # db.commit()
                    # db.refresh(database_value)
                else:
                    database_value = static_value

            # Update the relationship with the newly created object
            obj_in_data[relationship] = database_value

        return obj_in_data

    def validate_types(self):
        print(self.__class__.__orig_bases__)
        # Get the runtime value of the schemas attached to this class
        base_class_args = [
            base_class
            for base_class in self.__class__.__orig_bases__
            if base_class.__origin__ == StoreBase
        ]
        if not base_class_args:
            raise ValueError("StoreBase must be subclassed with type arguments")

        _, create_schema, update_schema = get_args(base_class_args[0])

        def validate_arg_model_order(args):
            """
            Ensure that models are declared before their SQLAlchemy counterparts. Otherwise
            objects will be cast as schemas where we typically want them to remain as SQLAlchemy objects.
            """
            index_of_model = [
                i for i, x in enumerate(args) if isclass(x) and issubclass(x, Base)
            ]
            if index_of_model:
                if min(index_of_model) > 0:
                    raise ValueError(
                        f"SQLAlchemy Model must come first in a list of typehints, actual order: {args}"
                    )

            # Recursively do this for all union types
            for arg in args:
                if isinstance(arg, types.UnionType):
                    validate_arg_model_order(arg.__args__)

        # Get all the nested elements that involve models and
        for schema in [create_schema, update_schema]:
            # Iterate over all typehints for the class
            schema_typehints = get_type_hints(schema)
            print(schema_typehints)

            for typehint in schema_typehints.values():
                if hasattr(typehint, "__args__"):
                    validate_arg_model_order(typehint.__args__)


class StoreFilterMixin(Generic[ModelType, FilterSchemaType], StoreGlobal[ModelType]):
    """
    A mixin to add simple exact-match filtering to a store.

    """

    archived_column_name = "archived"

    def get_multi(
        self,
        db: Session,
        filter: FilterSchemaType,
        skip: int | None = 0,
        limit: int | None = None,
        include_archived: bool = False,
        only_fetch_columns: list[Column] | None = None,
    ) -> list[ModelType]:
        query: Query

        if only_fetch_columns:
            query = db.query(*only_fetch_columns)
        else:
            query = db.query(self.model)

        query = self.build_filter(query, filter, include_archived)
        query = self._order_by(query)

        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def count_multi(
        self,
        db: Session,
        filter: FilterSchemaType,
        include_archived: bool = False,
    ):
        query = db.query(self.model)
        query = self.build_filter(query, filter, include_archived)
        return query.count()

    def build_filter(
        self, query: Query, filter: FilterSchemaType, include_archived: bool
    ):
        model_table: Table = getattr(self.model, "__table__")
        model_columns = model_table.columns

        for field, value in filter.dict(exclude_unset=True).items():
            # Split our special suffixes, if present
            parsed_field = field.split("__")
            raw_field = parsed_field[0]
            logic_type = parsed_field[1] if len(parsed_field) > 1 else None

            if raw_field not in model_columns:
                raise ValueError(f"Model `{self.model}` has no column `{field}`")

            if logic_type is None:
                query = query.filter(getattr(self.model, raw_field) == value)
            elif logic_type == "not":
                query = query.filter(getattr(self.model, raw_field) != value)
            elif logic_type == "in":
                query = query.filter(getattr(self.model, raw_field).in_(value))
            else:
                raise ValueError(
                    f"Key special suffix `{logic_type}` in `{field}` is not supported"
                )

        # Only allow include_archived behavior if the model has an archived column
        model_column_names = [column.name for column in model_columns]
        if self.archived_column_name in model_column_names:
            if include_archived:
                query = query.execution_options(include_archived=True)

        return query
