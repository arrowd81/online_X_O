from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'postgresql://test_db:123456@localhost:5532/test_db'

engine = create_engine(DATABASE_URL)
Session = sessionmaker(autoflush=False, autocommit=False, bind=engine)
base = declarative_base()
