from os.path import join, dirname, abspath
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

root = dirname(dirname(abspath(__file__)))
db_name = join(root, 'status.db')

__engine = create_engine(f'sqlite:////{db_name}', convert_unicode=True)
db_session = scoped_session(sessionmaker(bind=__engine, autocommit=False, autoflush=False))

Base = declarative_base()
Base.query = db_session.query_property()


def db_init():
    try:
        Base.metadata.create_all(bind=__engine)
        return True
    except:
        return False
