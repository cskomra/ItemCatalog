import sys

from sqlalchemy import Column, ForeignKey, Integer, String, Date, Enum

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

Base = declarative_base()
########## end beginning configuration code ##########
# Write class code here...

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'picture': self.picture
        }

class Event(Base):
    __tablename__ = "event" # SQL table name
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    date = Column(Date)
    eventType = Column(String(80))
    location = Column(String(80))
    description = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        #Returns object data in easily serializable format
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'description': self.description
        }

class Telling(Base):
    __tablename__ = "telling"
    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    description = Column(String(250))
    mediaFilepath = Column(String(150))
    event_id = Column(Integer, ForeignKey('event.id'))
    event = relationship(Event)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        #Returns object data in easily serializable format
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'mediaFilepath': self.mediaFilepath
        }

########## begin ending configuration code ##########
# a new db file will be created called 'lifrary.db'
engine = create_engine('sqlite:///lifrary.db')

Base.metadata.create_all(engine)