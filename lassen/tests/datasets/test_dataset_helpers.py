from dataclasses import dataclass
from functools import partial

import pandas as pd
import pytest
from datasets import Dataset

from lassen.datasets.dataset_helpers import batch_to_examples, examples_to_batch


@dataclass
class BatchInsertion:
    texts: list[str]


def batch_process(examples, explicit_schema: bool):
    new_examples: list[BatchInsertion] = []
    for example in batch_to_examples(examples):
        new_examples.append(BatchInsertion(example["raw_text"].split()))
    return examples_to_batch(
        new_examples, BatchInsertion, explicit_schema=explicit_schema
    )


def test_examples_to_batch():
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
            partial(batch_process, explicit_schema=False),
            batched=True,
            batch_size=1,
            num_proc=1,
            remove_columns=dataset.column_names,
        )

    dataset_new = dataset = dataset.map(
        partial(batch_process, explicit_schema=True),
        batched=True,
        batch_size=1,
        num_proc=1,
        remove_columns=dataset.column_names,
    )

    assert len(dataset_new) == 3
