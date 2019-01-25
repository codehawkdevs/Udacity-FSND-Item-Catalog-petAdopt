#!/usr/bin/env python3

import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import backref
from flask import session as login_session

Base = declarative_base()


# Class for creating a table named user.
class User(Base):
    __tablename__ = 'user'

    name = Column(String(80))
    email = Column(String(80))
    img_url = Column(String(500))
    id = Column(Integer, primary_key=True)


# Class for creating a table named pets.
class Pets(Base):
    __tablename__ = 'pets'

    category = Column(String(80), nullable=False,)
    id = Column(Integer, primary_key=True)
    img_url = Column(String(500), nullable=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    # ON DELETE CASCADE implemented
    # which delete all items when a category is deleted
    child = relationship("PetSub", backref="parent", cascade="all,delete")

    @property
    # Return object data in easily serializeable format
    def serialize(self):
        return {
            'id': self.id,
            'category': self.category,
            'img_url': self.img_url,
            'user_id': self.user_id
        }


# Class for creating a table named pet_sub.
class PetSub(Base):
    __tablename__ = 'pet_sub'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    breed = Column(String(80))
    description = Column(String(200))
    img_url = Column(String(500), nullable=True)
    location = Column(String(80))
    pet_id = Column(Integer, ForeignKey('pets.id', ondelete='CASCADE'))
    pets = relationship(Pets)
    owner = Column(String(80))
    medical_record_info = Column(String(200))
    gender = Column(String(1))
    contact = Column(Integer)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    # Return object data in easily serializeable format.
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'gender': self.gender,
            'breed': self.breed,
            'medical_record_info': self.medical_record_info,
            'owner': self.owner,
            'contact': self.contact,
            'location': self.location,
            'img_url': self.img_url,
            'user_id': self.user_id
        }

engine = create_engine('sqlite:///petadopt.db')
Base.metadata.create_all(engine)
