import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# database
database_location = os.environ.get('DATABASE_LOCATION')
username = os.environ.get('DATABASE_USERNAME')
password = os.environ.get('DATABASE_PASSWORD')
database_name = os.environ.get('DATABASE_NAME')
DATABASE_URL = f'postgresql://{username}:{password}@db/{database_name}'
print(DATABASE_URL)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(autoflush=False, autocommit=False, bind=engine)
base = declarative_base()
