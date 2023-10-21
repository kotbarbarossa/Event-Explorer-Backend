from sqlalchemy import Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class Command(Base):
    __tablename__ = 'commands'

    id = Column(Integer, primary_key=True, index=True)
    command = Column(String, unique=True, index=True)
    response = Column(String)

    def __init__(self, command: str, response: str):
        self.command = command
        self.response = response


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, unique=True, index=True)
    response = Column(String)

    def __init__(self, command: str, response: str):
        self.command = command
        self.response = response
