from dataclasses import dataclass
from functools import partial

import pandas as pd
import pytest
from datasets import Dataset

from lassen.datasets.dataset_helpers import batch_to_examples, examples_to_batch


@dataclass
class BatchInsertion:
    texts: list[str]


def batch_process(
    examples,
    ignore_empty: bool,
    explicit_schema: bool,
):
    new_examples: list[BatchInsertion] = []
    for example in batch_to_examples(examples):
        new_examples.append(BatchInsertion(example["raw_text"].split()))

    if ignore_empty:
        new_examples = [example for example in new_examples if len(example.texts) > 0]

    return examples_to_batch(
        new_examples, BatchInsertion, explicit_schema=explicit_schema
    )


@pytest.mark.parametrize(
    "ignore_empty,expected_rows",
    [
        (True, 2),
        (False, 3),
    ],
)
def test_examples_to_batch(ignore_empty: bool, expected_rows: int):
    df = pd.DataFrame(
        [
            {"raw_text": ""},
            {"raw_text": "This is a test"},
            {"raw_text": "This is another test"},
        ]
    )

    dataset = Dataset.from_pandas(df)

    # datasets won't be able to typehint a dataset that starts with an empty example.
    with pytest.raises(TypeError, match="Couldn't cast array of type"):
        dataset = dataset.map(
            partial(batch_process, explicit_schema=False, ignore_empty=False),
            batched=True,
            batch_size=1,
            num_proc=1,
            remove_columns=dataset.column_names,
        )

    dataset_new = dataset = dataset.map(
        partial(batch_process, explicit_schema=True, ignore_empty=ignore_empty),
        batched=True,
        batch_size=1,
        num_proc=1,
        remove_columns=dataset.column_names,
    )

    assert len(dataset_new) == expected_rows


def test_batch_to_examples():
    dataset_iteration = {"raw_text": ["value1", "value2"]}

    per_example = list(batch_to_examples(dataset_iteration))

    assert per_example == [{"raw_text": "value1"}, {"raw_text": "value2"}]


def test_cast_empty_batch():
    """
    Ensure we correctly can cast empty batches by using the explicit_schema flag.

    """
    examples_to_batch([], BatchInsertion, explicit_schema=True)
