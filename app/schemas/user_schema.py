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
    passwordConfirm: str
    role: str = 'user'
    verified: bool = True
    verification_code: str = None


class LoginUserSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


class UserResponse(UserBaseSchema):
    id: uuid.UUID
    
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
    
    verified: bool = False
    verification_code: str = None
    
    role: str = 'user'
    
    created_at: datetime
    updated_at: datetime

class FilteredUserResponse(UserBaseSchema):
    id: uuid.UUID = None