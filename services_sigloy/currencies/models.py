from sqlalchemy import Column, String, Integer
from sqlalchemy.sql.sqltypes import Boolean

from common.resources.tables import table_names
from db.pgsql.engine import Base


class Currency(Base):
    __tablename__ = table_names["currencies"]
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    short_name = Column(String(6))
    full_name = Column(String(16))
    networks = Column(String)
    markets = Column(String)
    rank = Column(Integer)
    is_stable = Column(Boolean, default=False)

    def update_columns(self, **columns):
        for key, value in columns.items():
            setattr(self, key, value)
    
    def __repr__(self) -> str:
        return super().__repr__()
