import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import TIMESTAMP, Column, ForeignKey, String, Boolean, text, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    firstname = Column(String,  nullable=True)
    lastname = Column(String,  nullable=True)
    street_address = Column(String,  nullable=True)
    postal_code = Column(String,  nullable=True)
    
    city_code = Column(String,  nullable=True)
    city = Column(String,  nullable=True)
    
    state_code = Column(String,  nullable=True)
    state = Column(String,  nullable=True)
    
    country_code = Column(String,  nullable=True)
    country = Column(String,  nullable=True)
    
    phone_number = Column(String, unique=True, nullable=True)
    photo = Column(String, nullable=True)
    
    secondary_contact = Column(String, nullable=True)
    secondary_contact_number = Column(String, nullable=True)
    
    verified = Column(Boolean, nullable=False, server_default='False')
    verification_code = Column(String, nullable=True)
    
    role = Column(String, server_default='user', nullable=False)
    
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    
    otp = Column(String, nullable=True)
    otp_secret = Column(String, nullable=True)
    otp_created_at = Column(TIMESTAMP(timezone=True),nullable=True)
    
    status = Column(String, nullable=True, server_default='active')
    
    created_at = Column(TIMESTAMP(timezone=True),nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True),nullable=False, server_default=text("now()"))
    
    
    pets = relationship('Pet', back_populates='owner', uselist=True)

    def to_dict(self):
            # Convert the User instance to a dictionary
            user_dict = {column.name: getattr(self, column.name) for column in self.__table__.columns}
            
            # Convert UUID to string
            user_dict['id'] = str(user_dict['id']) if user_dict['id'] else None

            # Convert datetime objects to string
            user_dict['created_at'] = user_dict['created_at'].isoformat() if user_dict['created_at'] else None
            user_dict['updated_at'] = user_dict['updated_at'].isoformat() if user_dict['updated_at'] else None
            user_dict['otp_created_at'] = user_dict['otp_created_at'].isoformat() if user_dict['otp_created_at'] else None

            return user_dict

class PetType(Base):
    __tablename__ = 'pet_type'
    
    type_id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True),nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True),nullable=False, server_default=text("now()"))
    
class Pet(Base):
    __tablename__ = 'pets'

    id = Column(Integer, primary_key=True)
    unique_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=False, nullable=False)

    microchip_id = Column(String, unique=False, nullable=True, index=True)
    name = Column(String, nullable=True, index=True)
    description = Column(String, nullable=True)
    behavior = Column(String, nullable=True)
    weight = Column(Float, nullable=True)
    gender = Column(String, nullable=True)
    color = Column(String, nullable=True)
    pet_type_id = Column(Integer, ForeignKey('pet_type.type_id'), nullable=True)
    main_picture = Column(String, nullable=True)
    breed = Column(String, nullable=True)
    date_of_birth_month = Column(Integer, nullable=True)
    date_of_birth_year = Column(Integer, nullable=True)

    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=True)

    pet_type = relationship('PetType')
    owner = relationship('User', back_populates='pets')

    pet_images = relationship('PetImages', back_populates='pet_owner')


class PetImages(Base):
    __tablename__ = 'pet_images'

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    
    path = Column(String(255), nullable=False)
    pet_id = Column(Integer, ForeignKey('pets.id'), primary_key=True)
    
    created_at = Column(TIMESTAMP(timezone=True),nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True),nullable=False, server_default=text("now()"))

    pet_owner = relationship('Pet', back_populates='pet_images')

class Post(Base):
    __tablename__ = 'posts'
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False,default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    category = Column(String, nullable=False)
    image = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    user = relationship('User')

class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False,default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rate = Column(Integer, nullable=False)
    comment = Column(String, nullable=False)
    display_flag = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    user = relationship('User')
    
class UserSettings(Base):
    __tablename__ = 'settings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False,default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    account = Column(String, nullable=True)
    security = Column(String, nullable=True)
    notification = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    user = relationship('User')