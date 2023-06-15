from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd
import pytest
from pyarrow import Table
from pyarrow.lib import ArrowInvalid

from lassen.datasets.pyarrow_schemas import get_schema_from_dataclass


@dataclass
class EmbeddedDataclass:
    value: int


@pytest.mark.parametrize(
    "field_type, field_value",
    [
        (
            int,
            1,
        ),
        (
            str,
            "test",
        ),
        (
            float,
            1.0,
        ),
        (
            np.ndarray[np.int32],  # type: ignore
            np.array([1, 2, 3], dtype=np.int32),
        ),
        (
            np.ndarray[np.float32],  # type: ignore
            np.array([1.0, 2.0, 3.0], dtype=np.float32),
        ),
        (
            list[str],
            ["test", "test2"],
        ),
        (
            EmbeddedDataclass,
            EmbeddedDataclass(value=1),
        ),
        (
            bool,
            True,
        ),
    ],
)
def test_get_schema_from_dataclass(field_type: Any, field_value: Any):
    """
    Ensure we can correctly convert a dataclass to a pyarrow schema and then cast
    the dataclass object into a table. If this fails it will raise a pyarrow.lib.ArrowInvalid.

    """

    @dataclass
    class ExampleSchema:
        field: field_type

    instance = ExampleSchema(field=field_value)
    schema = get_schema_from_dataclass(ExampleSchema)

    try:
        Table.from_pandas(pd.DataFrame([asdict(instance)]), schema=schema)
    except ArrowInvalid:
        pytest.fail("Unexpected pyarrow.lib.ArrowInvalid, unable to cast...")
