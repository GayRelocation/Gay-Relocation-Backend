from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.ext.declarative import as_declarative

@as_declarative()
class Base:
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}