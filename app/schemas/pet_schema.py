from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, constr
from app.schemas.user_schema import FilteredUserResponse, CreateUserSchema, PetDetailsUserResponse
import uuid
class Allergies(BaseModel):
    allergy: str 
    symptoms: str 
    class Config:
        orm_mode = True
    
class Medications(BaseModel):
    name: str
    brand: str
    dosage: str
    prescription: str
    class Config:
        orm_mode = True
    
class Vaccines(BaseModel):
    name: str
    type: str
    clinic: str
    date: datetime | str
    class Config:
        orm_mode = True
    
class PetBaseSchema(BaseModel):
    microchip_id: str | None  = None
    name: str | None  = None
    description: str | None  = None
    behavior: str | None  = None
    weight: float | None  = None
    gender: str | None  = None
    color: str | None  = None
    pet_type_id: int | None  = None
    main_picture: str | None  = None
    breed: str | None  = None
    date_of_birth_month: int | None  = None
    date_of_birth_year: int | None  = None
    owner_id: UUID | None = None
    no_of_scans: int | None = 0
    
    allergies: str = None
    medications: str = None
    vaccines: str = None

    class Config:
        orm_mode = True


class CreatePetSchema(PetBaseSchema):
    pass


class PetResponse(PetBaseSchema):
    id: int
    unique_id: UUID
    owner: FilteredUserResponse = None
    created_at: datetime
    updated_at: datetime

class PetResponse2(PetBaseSchema):
    id: int
    unique_id: UUID
    created_at: datetime = None
    updated_at: datetime = None

class UpdatePetSchema(PetBaseSchema):
    unique_id: UUID
    
    class Config:
        orm_mode = True


class ListPetResponse(BaseModel):
    status: str
    results: int
    pets: List[PetResponse]


class PetRegisterModel(BaseModel):
    firstname: str 
    lastname: str
    email: EmailStr
    phone_number: str
    
    state_code: str
    state: str
    
    city_code: int
    city: str
    
    street_address: str
    postal_code: str
    
    secondary_contact: str
    secondary_contact_number: str
    
    password: str
    confirm_password: str
    
    verified: bool = False
    verification_code: str | None = None
    role: str = "User"
    
    photo: str | None = None
    
    country_code: str = "AU"
    country: str = "Australia"
    
    
    name: str
    breed: str
    pet_type_id: int
    microchip_id: str
    unique_id: str
    main_picture: str | None = None
    color: str
    gender: str
    date_of_birth_year: int
    date_of_birth_month: int
    weight: int
    behavior: str | None = None
    description: str | None = None

class PetTypeResponse(BaseModel):
    type_id: str = None
    type: str = None

    class Config:
        orm_mode = True
        
class FilteredPetResponse(BaseModel):
    pet: PetResponse2
    owner: PetDetailsUserResponse = None
    pet_type: PetTypeResponse = None