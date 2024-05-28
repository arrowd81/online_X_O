from sqlalchemy import Column, Integer, String

from config import base


class User(base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
