from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine('sqlite:///data/data.sqlite')
session_factory = sessionmaker(bind=engine)
DBSession = scoped_session(session_factory)


class _Base(object):
    query = DBSession.query_property()


Base = declarative_base(cls=_Base)

