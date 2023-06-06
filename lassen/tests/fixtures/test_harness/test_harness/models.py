from sqlalchemy import Column, Integer, String

from lassen.db.base_class import Base


class SimpleModel(Base):
    __tablename__ = "simple_model"
    id = Column(Integer, primary_key=True)
    name = Column(String)
