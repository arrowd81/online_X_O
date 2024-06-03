import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# database
database_location = os.environ.get('DATABASE_LOCATION') or "localhost:5532"
username = os.environ.get('DATABASE_USERNAME') or "test_db"
password = os.environ.get('DATABASE_PASSWORD') or "123456"
database_name = os.environ.get('DATABASE_NAME') or "test_db"
DATABASE_URL = f'postgresql://{username}:{password}@{database_location}/{database_name}'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(autoflush=False, autocommit=False, bind=engine)
base = declarative_base()
