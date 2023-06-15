from dataclasses import is_dataclass
from types import NoneType
from typing import Type, Union, get_args, get_origin

import numpy as np
import pyarrow as pa

from lassen.shared import DataclassType

numpy_pyarrow_type_mapping = {
    np.dtype("int32"): pa.int32(),
    np.dtype("int64"): pa.int64(),
    np.dtype("float32"): pa.float32(),
    np.dtype("float64"): pa.float64(),
}

python_type_to_pyarrow = {
    int: pa.int32(),
    float: pa.float32(),
    str: pa.string(),
    bool: pa.bool_(),
}


def python_type_to_pyarrow_type(python_type: Type) -> Union[pa.DataType, None]:
    """
    Returns the corresponding pyarrow type for a Python type.
    """
    origin = get_origin(python_type)
    if origin is None:
        # This is not a complex type
        if python_type in python_type_to_pyarrow:
            return python_type_to_pyarrow[python_type]
        elif python_type is NoneType:
            return pa.null()
        elif is_dataclass(python_type):
            # This is a nested dataclass
            # Process the fields of the dataclass recursively
            fields = {
                key: python_type_to_pyarrow_type(val)
                for key, val in python_type.__annotations__.items()
            }
            return pa.struct(fields)
        elif python_type is np.ndarray:
            raise ValueError(
                "ndarrays should be typehinted with their inner type, like np.ndarray[np.int32]"
            )
        else:
            raise ValueError(
                f"Unsupported pyarrow field conversion type: {python_type}"
            )
    else:
        # This is a complex type, like list[str] or dict[str, str]
        if origin is list:
            # Get the type of the list elements
            args = get_args(python_type)
            if len(args) != 1:
                raise ValueError(
                    f"List must have exactly one type argument, received: {args}"
                )
            element_type = python_type_to_pyarrow_type(args[0])
            return pa.list_(element_type)
        elif origin is np.ndarray:
            args = get_args(python_type)
            if len(args) != 1:
                raise ValueError(
                    f"np.ndarray must have exactly one type argument, received: {args}"
                )
            numpy_dtype = args[0]
            pyarrow_type = numpy_pyarrow_type_mapping[np.dtype(numpy_dtype)]
            return pa.list_(pyarrow_type)
        else:
            raise ValueError(f"Unsupported pyarrow field conversion origin: {origin}")


def get_schema_from_dataclass(dataclass_instance: Type[DataclassType]) -> pa.Schema:
    """
    Generates a pyarrow.Schema instance from a dataclass instance.
    """
    if not is_dataclass(dataclass_instance):
        raise ValueError("Provided object is not a dataclass instance.")

    annotations = dataclass_instance.__annotations__
    schema = pa.schema(
        {key: python_type_to_pyarrow_type(val) for key, val in annotations.items()}
    )

    return schema
