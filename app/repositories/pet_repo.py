import os
from pathlib import Path
import shutil
from typing import List
import uuid

from pydantic import EmailStr
from sqlalchemy import select, update

from app import utils
from app.email import Email
from app.schemas.user_schema import CreateUserSchema, FilteredUserResponse
from .. import models
from ..schemas.pet_schema import FilteredPetResponse, PetBaseSchema, PetRegisterModel, PetResponse, ListPetResponse, CreatePetSchema, PetTypeResponse, UpdatePetSchema
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, UploadFile, status, APIRouter, Response
from ..database import get_session
from app.oauth2 import require_user
from ..repositories import user_repo

router = APIRouter()


USERDATA_DIR = os.path.join("app", "userdata")

# get pets without authentication
async def get_pets(db: Session, limit: int, page: int, search: str):
    skip = (page - 1) * limit

    query = await db.execute(
            select(models.Pet)
            .group_by(models.Pet.id)
            .limit(limit)
            .offset(skip)
        )
    pets = query.scalars().all()
    return {'status': 'success', 'results': len(pets), 'pets': pets}

# get pets with authentication
async def get_my_all_pets(db: Session, user_id: str):
    query = await db.execute(
            select(models.Pet)
            .group_by(models.Pet.id)
            .where(models.Pet.owner_id == user_id)
    )
    pets = query.scalars().all()
    return {'status': 'success', 'results': len(pets), 'pets': pets}

# get pets with authentication
async def get_pet_types(db: Session) -> List[PetTypeResponse]:
    query = await db.execute(
            select(models.PetType)
    )
    pets = query.scalars().all()
    return pets

# create pet without authentication
async def create_pet(pet: CreatePetSchema, db: Session):
    new_pet = models.Pet(**pet.dict())
    db.add(new_pet)
    db.commit()
    db.refresh(new_pet)
    return new_pet

# update pet without authentication
async def update_pet(id: str, pet: UpdatePetSchema, db: Session):
    # pet_query = db.query(models.Pet).filter(models.Pet.unique_id == id)
    # updated_pet = pet_query.first()
    pet_query = await db.execute(
            select(models.Pet).where(models.Pet.unique_id == id)
        )
    selected_pet = pet_query.scalar_one_or_none()
    if not selected_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Pet not found')
        
    if selected_pet is not None:
            for key, value in pet.dict(exclude_unset=True).items():
                setattr(selected_pet, key, value)
            await db.commit()
    return selected_pet

# update pet with authentication
async def update_my_pet(id: str, pet: UpdatePetSchema, db: Session, user_id: str):
    # pet_query = db.query(models.Pet).filter(models.Pet.unique_id == id, models.Pet.owner_id == user_id)
    # updated_pet: PetBaseSchema = pet_query.first()
    
    pet_query = await db.execute(
            select(models.Pet).where(models.Pet.unique_id == id)
        )
    updated_pet:PetBaseSchema = pet_query.scalar_one_or_none()

    if not updated_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Pet not found')
    if pet.owner_id != uuid.UUID(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not allowed to perform this action')
    if updated_pet is not None:
            for key, value in pet.dict(exclude_unset=True).items():
                setattr(updated_pet, key, value)
            await db.commit()
    return updated_pet

# update pet with authentication
async def update_my_pet_formdata(user_id: str, pet: UpdatePetSchema, file: UploadFile, db: Session):
    
    unique_filename = await cleanstr(file.filename)
    pet_profile_path = os.path.join(USERDATA_DIR, str(user_id), str(pet.unique_id), "profile") 
    final_filename =  os.path.join(pet_profile_path, unique_filename)
    pet.main_picture = final_filename.replace("app", "", 1)
    
    
    updated_pet = await update_pet(pet.unique_id, pet, db)
    
    # Pet profile picture path
    pet_profile_path = os.path.join(USERDATA_DIR, str(user_id), str(pet.unique_id), "profile") 
    
    # Create the path 
    Path(pet_profile_path).mkdir(parents=True, exist_ok=True)
    
    # Read and copy the file
    with open(os.path.join(pet_profile_path, unique_filename), 'w+b') as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    buffer.close()
    
    return updated_pet

# update pet without authentication
async def get_pet(id: str, db: Session):
    try:
        query = (
            select(models.Pet, models.User, models.PetType)
            .join(models.User, models.Pet.owner_id == models.User.id, isouter=True)  # Use isouter=True for a left join
            .join(models.PetType, models.Pet.pet_type_id == models.PetType.type_id, isouter=True)  # Add an outer join for PetType as well if needed
            .where(models.Pet.unique_id == id)
        )
        result = await db.execute(query)
        pet, user, pet_type = result.first()
        # return result.first()
        if not pet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Pet not found')
        return FilteredPetResponse(pet=pet, owner=user, pet_type=pet_type)
    except Exception as e:
        # Log the exception or handle it appropriately
        raise HTTPException(status_code=404, detail="Pet not found")
    
async def check_pet(id: str, db: Session):
    pet_query = await db.execute(
            select(models.Pet).where(models.Pet.unique_id == id)
        )
    selected_pet = pet_query.scalar_one_or_none()
    if not selected_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Pet not found')
    return selected_pet

# get pets with authentication
async def get_my_pet(id: str, user_id: str, db: Session,):
    # pet = db.query(models.Pet).filter(models.Pet.unique_id == id, models.Pet.owner_id == user_id).first()
    # if not pet:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
    #                         detail=f"Pet details not found")
    
    pet_query = await db.execute(
            select(models.Pet).where(models.Pet.unique_id == id, models.Pet.owner_id == user_id)
        )
    selected_pet = pet_query.scalar_one_or_none()
    if not selected_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Pet not found')
    return selected_pet

# update pet with authentication
async def delete_pet(id: str, db: Session, user_id: str):
    pet_query = db.query(models.Pet).filter(models.Pet.id == id)
    pet: PetBaseSchema = pet_query.first()
    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No pet with this id: {id} found')

    if str(pet.owner_id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not allowed to perform this action')
    pet_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

async def register_pet(user: CreateUserSchema, pet: UpdatePetSchema, file: UploadFile,  db: Session):
    
    
    unique_filename = await cleanstr(file.filename)
    new_user = await user_repo.add_user(db, user)
    
    
    pet_profile_path = os.path.join(USERDATA_DIR, str(new_user.id), str(pet.unique_id), "profile") 
    
    final_filename =  os.path.join(pet_profile_path, unique_filename)
    pet.owner_id = new_user.id
    pet.main_picture = final_filename.replace("app", "", 1)
    updated_pet = await update_pet(pet.unique_id, pet, db)
    
    # Pet profile picture path
    pet_profile_path = os.path.join(USERDATA_DIR, str(new_user.id), str(pet.unique_id), "profile") 
    
    # Create the path 
    Path(pet_profile_path).mkdir(parents=True, exist_ok=True)
    
    # Read and copy the file
    with open(os.path.join(pet_profile_path, unique_filename), 'w+b') as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    buffer.close()
        
    return {"user": new_user, "pet": updated_pet}
    # return {'status': 'success', 'message': 'Verification token successfully sent to your email'}
    
    
async def register_pet_no_file(user: CreateUserSchema, pet: UpdatePetSchema,  db: Session):
    
    new_user = await user_repo.add_user(db, user)
    pet.owner_id = new_user.id
    updated_pet = await update_pet(pet.unique_id, pet, db)
        
    return {"user": new_user, "pet": updated_pet}
    # return {'status': 'success', 'message': 'Verification token successfully sent to your email'}
    
   
    
async def cleanstr(filename):
    # Remove special characters and whitespaces and convert to lowercase
    filename = ''.join(c for c in filename if c.isalnum() or c in ',._').lower()
    
    # Remove file extension and get length
    name, ext = os.path.splitext(filename)
    name_length = len(name)
    
    # Check conditions and return result
    if name_length <= 8:
        return filename
    elif name_length > 8:
        return name[:8] + ext