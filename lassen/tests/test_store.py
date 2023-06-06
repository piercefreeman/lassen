from sqlalchemy.orm import Session

from lassen.store import StoreBase
from lassen.tests.fixtures import (
    TestModel,
    TestSchema,
    TestSchemaCreate,
    TestSchemaUpdate,
)


def create_batch(db_session: Session, quantity: int = 1):
    create_identifiers = []
    for i in range(quantity):
        test_model = TestModel(name=f"Test Model {i}")
        db_session.add(test_model)
        db_session.flush()
        db_session.refresh(test_model)
        create_identifiers.append(test_model.id)
    return create_identifiers


def test_store_base_get(db_session: Session):
    test_model_id = create_batch(db_session, quantity=1)[0]

    store = StoreBase[TestSchema, TestSchemaCreate, TestSchemaUpdate](TestModel)
    # Test with a valid ID
    retrieved = store.get(db_session, id=test_model_id)
    assert retrieved is not None
    assert retrieved.id == test_model_id
    assert retrieved.name == f"Test Model 0"

    # Test with an invalid ID
    assert store.get(db_session, id=9999) == None


def test_store_base_get_multi(db_session: Session):
    create_batch(db_session, quantity=5)

    store = StoreBase[TestSchema, TestSchemaCreate, TestSchemaUpdate](TestModel)
    # Test without skip and limit
    retrieved = store.get_multi(db_session)
    assert len(retrieved) == 5

    # Test with skip
    retrieved = store.get_multi(db_session, skip=2)
    assert len(retrieved) == 3

    # Test with limit
    retrieved = store.get_multi(db_session, limit=2)
    assert len(retrieved) == 2

    # Test with skip and limit
    retrieved = store.get_multi(db_session, skip=1, limit=2)
    assert len(retrieved) == 2


def test_store_base_update(db_session: Session):
    test_model_id = create_batch(db_session, quantity=1)[0]

    store = StoreBase[TestSchema, TestSchemaCreate, TestSchemaUpdate](TestModel)
    update_schema = TestSchemaUpdate(id=test_model_id, name="Updated Name")
    db_obj = store.get(db_session, id=test_model_id)
    assert db_obj is not None

    updated = store.update(db_session, db_obj=db_obj, obj_in=update_schema)
    db_session.commit()
    assert updated.id == test_model_id
    assert updated.name == "Updated Name"


def test_store_base_remove(db_session):
    test_model_id = create_batch(db_session, quantity=1)[0]

    store = StoreBase[TestSchema, TestSchemaCreate, TestSchemaUpdate](TestModel)
    store.remove(db_session, id=test_model_id)
    db_session.commit()

    # Test that the model instance has been removed
    assert store.get(db_session, id=test_model_id) is None
