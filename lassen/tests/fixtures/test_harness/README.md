# lassen-test-app

Note that we don't use this package directly. But we do lay it out as a package in case you need to generate more migrations automatically. To do this:

```sh
poetry install
poetry run pip install -e ..

createuser lassen_harness
createdb -O lassen_harness lassen_harness_db
```

Creating new migrations:

```sh
POSTGRES_USER=lassen_harness POSTGRES_DB=lassen_harness_db poetry run migrate revision --autogenerate --message "New migration"
```
