# lassen

**40.4881° N, 121.5049° W**

Core utilities for MonkeySee web applications.

Not guaranteed to be backwards compatible, use at your own risk.

## Structure

**Stores:** Each model is expected to have its own store. Base classes that provide standard logic are provided by `lassen.store`
- StoreBase: Base class for all stores
- StoreFilterMixin: Mixin for filtering stores that specify an additional schema to use to filter

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
poetry install

createuser lassen
createdb -O lassen lassen_db
createdb -O lassen lassen_test_db
```

Unit Tests:

```sh
poetry run pytest
```
