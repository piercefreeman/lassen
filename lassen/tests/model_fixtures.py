from pydantic import BaseModel
from sqlalchemy import Column, Integer, String

from lassen.db.base_class import Base


class TestModel(Base):
    __tablename__ = "testmodel"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)


class TestSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class TestSchemaCreate(TestSchema):
    pass


class TestSchemaUpdate(TestSchema):
    pass
