from datetime import datetime
from typing import List
from uuid import UUID
from pydantic import BaseModel, EmailStr, constr
from app.schemas.user_schema import FilteredUserResponse

    
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


class UpdatePetSchema(PetBaseSchema):
    unique_id: UUID
    
    class Config:
        orm_mode = True


class ListPetResponse(BaseModel):
    status: str
    results: int
    pets: List[PetResponse]


class PetRegisterModel(BaseModel):
    
    firstname:  str = None
    lastname:  str = None
    email:  str = None
    state:  str = None
    state_code:  str = None
    city:  str = None
    city_id:  str = None
    address:  str = None
    postal_code:  str = None
    phone_no:  str = None
    contact_person:  str = None
    contact_person_no:  str = None

    guid: UUID = None
    pet_type: int = None
    pet_gender:  str = None
    pet_name:  str = None
    pet_microchip_no: str = None
    pet_breed: str = None
    pet_weight: float = None
    pet_color:  str = None
    pet_birth_month: int = None
    pet_birth_year: int = None
    
    username: str = None
    password: str = None
