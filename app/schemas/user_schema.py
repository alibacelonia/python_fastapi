from datetime import datetime
from typing import List
import uuid
from pydantic import BaseModel, EmailStr, constr


class UserBaseSchema(BaseModel):
    firstname: str = None
    lastname: str = None
    email: EmailStr = None
    photo: str = None

    class Config:
        orm_mode = True


class CreateUserSchema(UserBaseSchema):
    street_address:str = None
    postal_code:str = None
    
    city_code: str = None
    city: str = None
    
    state_code: str = None
    state: str = None
    
    country_code: str = None
    country: str = None
    
    phone_number: str = None
    photo: str = None
    
    secondary_contact: str = None
    secondary_contact_number: str = None
    
    password: constr(min_length=8)
    passwordConfirm: constr(min_length=8)
    role: str = 'user'
    verified: bool = False
    verification_code: str = None
    
    otp: str = None
    otp_secret: str = None
    otp_created_at: datetime = None
    
    status: str = 'active'


class UpdateUserSchema(BaseModel):
    
    email: str = None
    
    firstname: str = None
    lastname: str = None
    
    street_address:str = None
    postal_code:str = None
    
    city_code: str = None
    city: str = None
    
    state_code: str = None
    state: str = None
    
    country_code: str = None
    country: str = None
    
    phone_number: str = None
    photo: str = None
    
    secondary_contact: str = None
    secondary_contact_number: str = None
    
    otp: str = None
    otp_secret: str = None
    otp_created_at: datetime = None


class LoginUserSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=8)

class ChangePasswordUserSchema(BaseModel):
    new_password: constr(min_length=8)
    confirm_password: constr(min_length=8)
    current_password: constr(min_length=8)

class UserResponse(UserBaseSchema):
    id: uuid.UUID
    
    street_address: str = None
    postal_code: str = None
    
    city_code: str = None
    city: str = None
    
    state_code: str = None
    state: str = None
    
    country_code: str = None
    country: str = None
    
    phone_number: str = None
    photo: str = None
    
    secondary_contact: str = None
    secondary_contact_number: str = None
    
    verified: bool = False
    verification_code: str = None
    
    otp: str = None
    otp_secret: str = None
    otp_created_at: datetime = None
    
    role: str = 'user'
    
    status: str = 'active'
    
    created_at: datetime
    updated_at: datetime

    def to_dict(self):
        user_response_dict = super().dict()

        # Convert UUID to string
        user_response_dict['id'] = str(user_response_dict['id']) if user_response_dict['id'] else None

        # Convert datetime objects to string
        user_response_dict['created_at'] = user_response_dict['created_at'].isoformat() if user_response_dict['created_at'] else None
        user_response_dict['updated_at'] = user_response_dict['updated_at'].isoformat() if user_response_dict['updated_at'] else None
        user_response_dict['otp_created_at'] = user_response_dict['otp_created_at'].isoformat() if user_response_dict['otp_created_at'] else None

        return user_response_dict


class FilteredUserResponse(UserBaseSchema):
    id: uuid.UUID = None
    
class EmailSchema(BaseModel):
    email: str
class PhoneSchema(BaseModel):
    phone: str
    
    
class PetDetailsUserResponse(BaseModel):
    email: str
    phone_number: str
    secondary_contact: str
    secondary_contact_number: str

    class Config:
        orm_mode = True