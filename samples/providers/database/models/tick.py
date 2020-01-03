from sqlalchemy import Column, DateTime, Float, Integer, String, Index

from . import Base


class Tick(Base):
    __tablename__ = 'ticks'

    id = Column(Integer, primary_key=True)
    epic = Column(String, nullable=False)  # epic_code as string
    datetime = Column(DateTime, nullable=False)
    bid = Column(Float, nullable=False)
    ask = Column(Float, nullable=False)


Index('idx_indice_datetime', Tick.epic, Tick.datetime)
