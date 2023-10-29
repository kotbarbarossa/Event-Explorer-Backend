from sqlalchemy import (Column, Integer, String,
                        MetaData, DateTime, Boolean,
                        Enum, Text, ForeignKey, Table,
                        CheckConstraint)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class Command(Base):
    """Модель команды."""
    __tablename__ = 'commands'

    id = Column(Integer, primary_key=True, index=True)
    command = Column(String, unique=True, index=True)
    response = Column(String)

    def __init__(self, command: str, response: str):
        self.command = command
        self.response = response


class Message(Base):
    """Модель сообщения."""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, unique=True, index=True)
    response = Column(String)

    def __init__(self, message: str, response: str):
        self.message = message
        self.response = response


user_subscriptions = Table(
    'user_subscriptions',
    Base.metadata,
    Column(
        'user_id',
        String,
        ForeignKey('users.telegram_id'),
        primary_key=True),
    Column(
        'subscriber_id',
        String,
        ForeignKey('users.telegram_id'),
        primary_key=True),

    CheckConstraint(
        ' user_id' != 'subscriber_id',
        name='check_unique_constraint'
    )
)

place_user_association = Table(
    'place_user_association',
    Base.metadata,
    Column(
        'place_id',
        String,
        ForeignKey('places.place_id'),
        primary_key=True),
    Column(
        'user_id',
        String,
        ForeignKey('users.telegram_id'),
        primary_key=True),
)

event_participants = Table(
    'event_participants',
    Base.metadata,
    Column(
        'event_id',
        Integer,
        ForeignKey('events.id'),
        primary_key=True),
    Column(
        'user_id',
        String,
        ForeignKey('users.telegram_id'),
        primary_key=True),
)


class User(Base):
    """Модель пользователя."""
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

    subscriptions = relationship(
        'User',
        secondary=user_subscriptions,
        primaryjoin=telegram_id == user_subscriptions.c.user_id,
        secondaryjoin=telegram_id == user_subscriptions.c.subscriber_id,
        back_populates='subscribers'
    )

    subscribers = relationship(
        'User',
        secondary=user_subscriptions,
        primaryjoin=telegram_id == user_subscriptions.c.subscriber_id,
        secondaryjoin=telegram_id == user_subscriptions.c.user_id,
        back_populates='subscriptions'
    )


class Place(Base):
    """Модель места."""
    __tablename__ = 'places'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=True)
    place_id = Column(String, unique=True, nullable=False, index=True)
    events = relationship('Event', back_populates='place')

    subscribers = relationship(
        'User',
        secondary=place_user_association,
        primaryjoin=place_id == place_user_association.c.place_id,
        secondaryjoin=User.telegram_id == place_user_association.c.user_id,
        back_populates='favorite_places',
    )


class Event(Base):
    """Модель события."""
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default='Событие')
    description = Column(Text, nullable=True)
    user_id = Column(String, ForeignKey('users.telegram_id'), nullable=False)
    place_id = Column(String, ForeignKey('places.place_id'), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    comment = Column(String, nullable=True)

    place = relationship('Place', back_populates='events')

    participants = relationship(
        'User',
        secondary=event_participants,
        primaryjoin=id == event_participants.c.event_id,
        secondaryjoin=User.telegram_id == event_participants.c.user_id,
        back_populates='events_participated',
    )


User.favorite_places = relationship(
    'Place',
    secondary=place_user_association,
    primaryjoin=User.telegram_id == place_user_association.c.user_id,
    secondaryjoin=place_user_association.c.place_id == Place.place_id,
    back_populates='subscribers',
)


User.events_participated = relationship(
        'Event',
        secondary=event_participants,
        primaryjoin=(User.telegram_id == event_participants.c.user_id),
        secondaryjoin=(event_participants.c.event_id == Event.id),
        back_populates='participants',
    )
