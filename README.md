# lassen

**40.4881° N, 121.5049° W**

Core utilities for MonkeySee web applications.

Not guaranteed to be backwards compatible, use at your own risk.

## Structure

**Stores:** Each model is expected to have its own store. Base classes that provide standard logic are provided by `lassen.store`
- StoreBase: Base class for all stores
- StoreFilterMixin: Mixin for filtering stores that specify an additional schema to use to filter

**Datasets:** Optional huggingface `datasets` processing utilities. Only installed under the `lassen[datasets]` extra. These provide support for:

- batch_to_examples: Iterate and manipulate each example separately, versus over nested key-based lists.
- examples_to_batch: Takes the output of a typehinted element-wise batch and converts into the format needed for dataset insertion. If datasets can't automatically interpret the type of the fields, also provide automatic casting based on the typehinted dataclass.

```python
from lassen.datasets import batch_to_examples, examples_to_batch
import pandas as pd

@dataclass
class BatchInsertion:
    texts: list[str]

def batch_process(examples):
    new_examples : list[BatchInsertion] = []
    for example in batch_to_examples(examples):
        new_examples.append(
            BatchInsertion(
                example["raw_text"].split()
            )
        )

    # datasets won't be able to typehint a dataset that starts with an empty example, so we use our explicit schema to cast the data
    return examples_to_batch(new_examples, BatchInsertion, explicit_schema=True)

df = pd.DataFrame(
    [
        {"raw_text": ""},
        {"raw_text": "This is a test"},
        {"raw_text": "This is another test"},
    ]
)

dataset = Dataset.from_pandas(df)

dataset = dataset.map(
    batch_process,
    batched=True,
    batch_size=1,
    num_proc=1,
    remove_columns=dataset.column_names,
)
```

**Migrations:** Lassen includes a templated alembic.init and env.py file. Client applications just need to have a `migrations` folder within their project root. After this you can swap `poetry run alembic` with `poetry run migrate`.

```sh
poetry run migrate upgrade head
```

**Settings:** Application settings should subclass our core settings. This provides a standard way to load settings from environment variables and includes common database keys.

```python
from lassen.core.config import CoreSettings, register_settings

@register_settings
class ClientSettings(CoreSettings):
    pass
```

**Schemas:** For helper schemas when returning results via API, see [lassen.schema](./lassen/schema.py).

## Development

```sh
poetry install --extras "datasets"

createuser lassen
createdb -O lassen lassen_db
createdb -O lassen lassen_test_db
```

Unit Tests:

```sh
poetry run pytest
```
