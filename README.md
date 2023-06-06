# lassen

**40.4881° N, 121.5049° W**

Core utilities for MonkeySee web applications.

Not guaranteed to be backwards compatible, use at your own risk.

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
