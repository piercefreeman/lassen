from dataclasses import asdict, fields
from typing import Any, Iterator, Type

import pandas as pd
from pyarrow import Table

from lassen.datasets.pyarrow_schemas import get_schema_from_dataclass
from lassen.shared import DataclassType


def batch_to_examples(batch: dict[str, list[Any]]) -> Iterator[dict[str, Any]]:
    """
    Batches are passed as dictionary-lists:

    {feature1: [values], feature2: [values]}

    It's typically more natural to treat a batch as each example. This function reformats
    into each separate examples in a streaming iterator.

    """
    lengths = {len(v) for v in batch.values()}
    if len(lengths) != 1:
        raise ValueError("All lists in the batch must have the same length.")

    for i in range(next(iter(lengths))):
        # Yield a dictionary that represents the i-th example in the batch.
        yield {feature: values[i] for feature, values in batch.items()}


def examples_to_batch(
    examples: Iterator[DataclassType] | list[DataclassType],
    data_class: Type[DataclassType],
    explicit_schema: bool = False,
) -> dict[str, list[Any]] | Table:
    """
    This function takes an iterator of examples and converts it into a batch.
    Each example is a dictionary of features:

    {"feature1": value, "feature2": value}

    The function returns a dictionary where each key corresponds to a feature and the value is a list of feature values for all examples.
    """
    # We create a placeholder series of lists here because `datasets` expects that each batch dictionary will
    # have the same keys, even if there are no objects. Trying to build this up as we go based on the examples
    # results in a blank dictionary if the values are empty.
    batch: dict[str, list[Any]] = {field.name: [] for field in fields(data_class)}

    for example in examples:
        # For each example, iterate over its features.
        for feature, value in asdict(example).items():
            batch[feature].append(value)

    if explicit_schema and examples:
        # If explicit_schema is specified without examples, the dataframe will have empty dtypes
        # by default and the schema-dataframe mismatch will raise an exception.
        schema = get_schema_from_dataclass(data_class)
        table = Table.from_pandas(pd.DataFrame(batch), schema=schema)
        return table
    else:
        return batch
