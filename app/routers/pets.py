from datetime import datetime
from typing import List, Optional
import uuid

from app.schemas.user_schema import CreateUserSchema
from .. import models
from ..schemas.pet_schema import PetBaseSchema, PetRegisterModel, PetResponse, ListPetResponse, CreatePetSchema, PetTypeResponse, UpdatePetSchema
from sqlalchemy.orm import Session
from fastapi import Depends, File, Form, HTTPException, Query, Request, UploadFile, status, APIRouter, Response
from ..database import get_session
from app.oauth2 import require_user
from ..repositories import pet_repo
import qrcode
from fastapi.responses import StreamingResponse
from io import BytesIO, StringIO
import zipfile

router = APIRouter()


@router.get('/')
async def get_pets(db: Session = Depends(get_session), limit: int = 10, page: int = 1, search: str = '', filters: str = ''):
    response = await pet_repo.get_pets(db, limit, page, search, filters)
    return response


@router.get('/mypets')
async def get_pets(db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    response = await pet_repo.get_my_all_pets(db, user_id)
    return response

@router.get('/pet-types')
async def get_pets(db: Session = Depends(get_session)):
    response = await pet_repo.get_pet_types(db)
    return [{'value': entry.type_id, 'label': entry.type} for entry in response]

@router.post('/', status_code=status.HTTP_201_CREATED, response_model=PetResponse)
async def create_pet(pet: CreatePetSchema, db: Session = Depends(get_session), owner_id: str = Depends(require_user)):
    # pet.user_id = uuid.UUID(owner_id)
    new_pet = models.Pet(**pet.dict())
    db.add(new_pet)
    await db.commit()
    await db.refresh(new_pet)
    return new_pet


@router.put('/{id}')
async def update_pet(id: str, pet: PetBaseSchema, db: Session = Depends(get_session)):
    response = await pet_repo.update_pet(id, pet, db)
    return response

@router.put('/{id}/update')
async def update_my_pet(id: str, pet: PetBaseSchema, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    pet.owner_id = uuid.UUID(user_id)
    # return pet
    response = await pet_repo.update_my_pet(id, pet, db, user_id)
    return response


@router.get('/{id}')
async def get_pet(id: str, db: Session = Depends(get_session)):
    response = await pet_repo.get_pet(id, db)
    return response

@router.get('/{id}/get_details')
async def get_pet(id: str, db: Session = Depends(get_session)):
    response = await pet_repo.check_pet(id, db)
    return response


@router.get('/{id}/check')
async def get_pet(id: str, db: Session = Depends(get_session)):
    response : PetBaseSchema = await pet_repo.check_pet(id, db)
    if response.owner_id is not None:
        data = {"has_owner": True}
    else:
        data = {"has_owner": False}
    return data

@router.get('/{id}/details')
async def get_pet(id: str, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    response = await pet_repo.get_my_pet(id, user_id, db)
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

@router.put('/register/')
async def register_pet( params: PetRegisterModel, request: Request, db: Session = Depends(get_session)):

    user = CreateUserSchema(
        firstname=params.firstname, 
        lastname=params.lastname, 
        email=params.email,
        state=params.state,
        state_code=params.state_code,
        city=params.city,
        city_code=params.city_code,
        street_address=params.street_address,
        postal_code=params.postal_code,
        phone_number=params.phone_number,
        secondary_contact=params.secondary_contact,
        secondary_contact_number=params.secondary_contact_number,
        password=params.password,
        passwordConfirm=params.confirm_password,
    )
    
    pet = UpdatePetSchema(
        unique_id=params.unique_id,
        microchip_id=params.microchip_id,
        name=params.name,
        breed=params.breed,
        gender=params.gender,
        pet_type_id=params.pet_type_id,
        weight=params.weight,
        color=params.color,
        date_of_birth_month=params.date_of_birth_month,
        date_of_birth_year=params.date_of_birth_year
    )

    # return {"user": user, "pet": pet}
    response = await pet_repo.register_pet_no_file(user, request, pet, db)
    return response

@router.post('/register')
async def register_pet(
    request: Request,
    guid: str = Form(...),
    firstname: str = Form(...),
    lastname: str = Form(...),
    email: str = Form(...),
    state: str = Form(...),
    state_code: str = Form(...),
    city: str = Form(...),
    city_code: str = Form(...),
    street_address: str = Form(...),
    postal_code: str = Form(...),
    phone_number: str = Form(...),
    secondary_contact: str = Form(...),
    secondary_contact_number: str = Form(...),
        
    behavior: Optional[str] = Form(default=None),  # Add the new fields here
    description: Optional[str] = Form(default=None),
    weight: str = Form(...),
    pet_type_id: str = Form(...),
    gender: str = Form(...),
    name: str = Form(...),
    microchip_id: str = Form(...),
    breed: str = Form(...),
    color: str = Form(...),
    date_of_birth_month: str = Form(...),
    date_of_birth_year: str = Form(...),
        
    password: str = Form(...),
    file: UploadFile = File(...), 
    db: Session = Depends(get_session),
):

    user = CreateUserSchema(
        firstname=firstname, 
        lastname=lastname, 
        email=email,
        state=state,
        state_code=state_code,
        city=city,
        city_code=city_code,
        street_address=street_address,
        postal_code=postal_code,
        phone_number=phone_number,
        secondary_contact=secondary_contact,
        secondary_contact_number=secondary_contact_number,
        password=password,
        passwordConfirm=password,
    )
    
    pet = UpdatePetSchema(
        unique_id=guid,
        behavior= behavior,  # Include the new fields here
        description= None if description == "None" else description,
        weight= weight,
        pet_type_id= pet_type_id,
        gender= gender,
        name= name,
        microchip_id= microchip_id,
        breed= breed,
        color= color,
        date_of_birth_month= date_of_birth_month,
        date_of_birth_year= date_of_birth_year,
        main_picture=file.filename if file else None
    )

    # return {"user": user, "pet": pet}
    response = await pet_repo.register_pet(user, pet, file, request, db)
    return response

# Update pet type by unique id
@router.post('/update')
async def update_pet_type(
    guid: str = Form(...),
    behavior: Optional[str] = Form(default=None),  # Add the new fields here
    description: Optional[str] = Form(default=None),
    weight: str = Form(...),
    pet_type_id: str = Form(...),
    gender: str = Form(...),
    name: str = Form(...),
    microchip_id: str = Form(...),
    breed: str = Form(...),
    color: str = Form(...),
    date_of_birth_month: str = Form(...),
    date_of_birth_year: str = Form(...),
    file: Optional[UploadFile] = File(default=None), 
    db: Session = Depends(get_session),
    user_id: str = Depends(require_user)
):
    
    data = UpdatePetSchema(
        unique_id=guid,
        behavior= behavior,  # Include the new fields here
        description= None if description == "None" else description,
        weight= weight,
        pet_type_id= pet_type_id,
        gender= gender,
        name= name,
        microchip_id= microchip_id,
        breed= breed,
        color= color,
        date_of_birth_month= date_of_birth_month,
        date_of_birth_year= date_of_birth_year,
        owner_id=user_id,
        main_picture=file.filename if file else None
    )
    
    # return data
    response = await pet_repo.update_my_pet_formdata(user_id, data, file, db)
    
    return response

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data("https://secure-petz.info/"+str(data))
    qr.make(fit=True)

    # Generate QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = BytesIO()
    img.save(img_bytes)
    img_bytes.seek(0)

    return img_bytes

@router.post('/generate_qr_zip')
async def generate_qr_zip(data: list):
    filtered_data = [item['unique_id'] for item in data]
    
    # return filtered_data
    # Create a ZIP file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        for item in filtered_data:
            # Generate QR code for each item and add it to the ZIP file
            qr_code_bytes = generate_qr_code(item)
            zip_file.writestr(f'qrcode_{item}.png', qr_code_bytes.read())

    # Move to the beginning of the ZIP buffer
    zip_buffer.seek(0)

    # Return the ZIP file as a response
    return StreamingResponse(zip_buffer, media_type="application/zip", headers={'Content-Disposition': 'attachment; filename=qr_codes.zip'})

@router.post('/generate-records')
async def generate_records(num_records: int = Query(..., title="Number of Records", ge=1, le=1000), db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    generated_pets = []
    for _ in range(num_records):
        pet_data = {
            "microchip_id": None,
            "name": None,
            "description": None,
            "behavior": None,
            "weight": None,
            "gender": None,
            "color": None,
            "pet_type_id": None,
            "main_picture": None,
            "breed": None,
            "date_of_birth_month": None,
            "date_of_birth_year": None,
            "owner_id": None
        }

        pet = models.Pet(**pet_data, created_at=datetime.utcnow(), created_by=user_id, updated_at=datetime.utcnow())
        db.add(pet)
        generated_pets.append(pet)

    await db.commit()
    return generated_pets