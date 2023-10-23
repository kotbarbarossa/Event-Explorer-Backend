from sqlalchemy import (Column, Integer, String,
                        MetaData, DateTime, Boolean,
                        # ForeignKey,
                        Enum)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
# from sqlalchemy.orm import relationship

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

    def __init__(self, message: str, response: str):
        self.message = message
        self.response = response


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    telegram_username = Column(String, index=True, default='', nullable=True)
    role = Column(Enum(
        'administrator',
        'moderator',
        'organizer',
        'participant',
        name='user_role'), default='participant')
    first_name = Column(String, default='', nullable=True)
    last_name = Column(String, default='', nullable=True)
    language_code = Column(String, default='', nullable=True)
    is_bot = Column(Boolean)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    modified_date = Column(DateTime(timezone=True), onupdate=func.now())
    comment = Column(String, default='', nullable=True)
