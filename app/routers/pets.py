import uuid

from app.schemas.user_schema import CreateUserSchema
from .. import models
from ..schemas.pet_schema import PetBaseSchema, PetRegisterModel, PetResponse, ListPetResponse, CreatePetSchema, UpdatePetSchema
from sqlalchemy.orm import Session
from fastapi import Depends, File, Form, HTTPException, UploadFile, status, APIRouter, Response
from ..database import get_session
from app.oauth2 import require_user
from ..repositories import pet_repo

router = APIRouter()


@router.get('/')
async def get_pets(db: Session = Depends(get_session), limit: int = 10, page: int = 1, search: str = ''):
    response = await pet_repo.get_pets(db, limit, page, search)
    return response


@router.get('/mypets')
async def get_pets(db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    response = await pet_repo.get_my_all_pets(db, user_id)
    return response

@router.post('/', status_code=status.HTTP_201_CREATED, response_model=PetResponse)
async def create_pet(pet: CreatePetSchema, db: Session = Depends(get_session), owner_id: str = Depends(require_user)):
    # pet.user_id = uuid.UUID(owner_id)
    new_pet = models.Pet(**pet.dict())
    db.add(new_pet)
    await db.commit()
    await db.refresh(new_pet)
    return new_pet


@router.put('/{id}', response_model=PetResponse)
async def update_pet(id: str, pet: UpdatePetSchema, db: Session = Depends(get_session)):
    response = pet_repo.update_pet(id, pet, db)
    return response

@router.put('/{id}/update', response_model=PetResponse)
async def update_pet(id: str, pet: UpdatePetSchema, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    response = pet_repo.update_my_pet(id, pet, db, user_id)
    return response


@router.get('/{id}', response_model=PetResponse)
async def get_pet(id: str, db: Session = Depends(get_session)):
    response = pet_repo.get_pet(id, db)
    return response

@router.get('/{id}/details', response_model=PetResponse)
async def get_pet(id: str, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    response = pet_repo.get_my_pet(id, db, user_id)
    return response


@router.delete('/{id}')
async def delete_pet(id: str, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    pet_query = db.query(models.Pet).filter(models.Pet.id == id)
    pet = pet_query.first()
    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No pet with this id: {id} found')

    if str(pet.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not allowed to perform this action')
    pet_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/register')
async def register_pet(
    guid: str = Form(...),
    firstname: str = Form(...),
    lastname: str = Form(...),
    email: str = Form(...),
    state: str = Form(...),
    state_code: str = Form(...),
    city: str = Form(...),
    city_id: str = Form(...),
    address: str = Form(...),
    postal_code: str = Form(...),
    phone_no: str = Form(...),
    contact_person: str = Form(...),
    contact_person_no: str = Form(...),
        
    pet_type: int = Form(...),
    pet_gender: str = Form(...),
    pet_name: str = Form(...),
    pet_microchip_no: str = Form(...),
    pet_breed: str = Form(...),
    pet_color: str = Form(...),
    pet_weight: float = Form(...),
    pet_birth_month: int = Form(...),
    pet_birth_year: int = Form(...),
        
    password: str = Form(...),
    file: UploadFile = File(...), 
    db: Session = Depends(get_session),
):
    # form_data = PetRegisterModel(
    #     guid=guid,
    #     firstname=firstname,
    #     lastname=lastname,
    #     email=email,    
    #     state=state,
    #     state_code=state_code,
    #     city=city,
    #     city_id=city_id,
    #     address=address,
    #     postal_code=postal_code,
    #     phone_no=phone_no,
    #     contact_person=contact_person,
    #     contact_person_no=contact_person_no,
        
    #     pet_type=pet_type,
    #     pet_gender=pet_gender,
    #     pet_name=pet_name,
    #     pet_microchip_no=pet_microchip_no,
    #     pet_weight=pet_weight,
    #     pet_breed=pet_breed,
    #     pet_color=pet_color,
    #     pet_birth_month=pet_birth_month,
    #     pet_birth_year=pet_birth_year,
        
    #     password=password)

    user = CreateUserSchema(
        firstname=firstname, 
        lastname=lastname, 
        email=email,
        state=state,
        state_code=state_code,
        city=city,
        city_code=city_id,
        street_address=address,
        postal_code=postal_code,
        phone_number=phone_no,
        secondary_contact=contact_person,
        secondary_contact_number=contact_person_no,
        password=password,
        passwordConfirm=password,
    )
    
    pet = UpdatePetSchema(
        unique_id=guid,
        microchip_id=pet_microchip_no,
        name=pet_name,
        breed=pet_breed,
        gender=pet_gender,
        pet_type_id=pet_type,
        weight=pet_weight,
        color=pet_color,
        date_of_birth_month=pet_birth_month,
        date_of_birth_year=pet_birth_year
    )

    # return {"user": user, "pet": pet}
    response = await pet_repo.register_pet(user, pet, file, db)
    return response
