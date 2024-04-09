from datetime import datetime
import json
from typing import List, Optional
import uuid

from sqlalchemy import desc, select
from app.email import Email
from app.schemas.notification_schema import CreateNotificationSchema, NotificationBaseSchema
from app.schemas.scan_schema import ScanSchema

from app.schemas.user_schema import CreateUserSchema, UserResponse
from .. import models
from ..schemas.pet_schema import Allergies, Medications, PetBaseSchema, PetRegisterModel, PetResponse, ListPetResponse, CreatePetSchema, PetTypeResponse, UpdatePetSchema, Vaccines
from sqlalchemy.orm import Session
from fastapi import Depends, File, Form, HTTPException, Query, Request, UploadFile, status, APIRouter, Response, BackgroundTasks
from ..database import get_session
from app.oauth2 import require_user
from ..repositories import pet_repo, scan_repo
import qrcode
from fastapi.responses import StreamingResponse
from io import BytesIO, StringIO
import zipfile

router = APIRouter()

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # Serialize datetime to ISO 8601 format
        return json.JSONEncoder.default(self, obj)

@router.get('/')
async def get_pets(db: Session = Depends(get_session), limit: int = 10, page: int = 1, search: str = '', filters: str = ''):
    response = await pet_repo.get_pets(db, limit, page, search, filters)
    return response


@router.get('/mypets')
async def get_pets(db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    response = await pet_repo.get_my_all_pets(db, user_id)
    return response


@router.get('/{owner_id}/list')
async def get_pets(owner_id: str, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    response = await pet_repo.get_pets_by_owner_id(owner_id, db)
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
    return pet

@router.put('/{id}/update')
async def update_my_pet(id: str, pet: PetBaseSchema, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    pet.owner_id = uuid.UUID(user_id)
    # return pet
    response = await pet_repo.update_my_pet(id, pet, db, user_id)
    return response

@router.post('/{id}/medical-info/delete')
async def update_my_pet_allergies(id: str, data: dict, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    pet_query = await db.execute(
            select(models.Pet).where(models.Pet.unique_id == id)
        )
    selected_pet:PetBaseSchema = pet_query.scalar_one_or_none()
    if not selected_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Pet not found')
    if selected_pet.owner_id != uuid.UUID(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not allowed to perform this action')
        
    if data['set'] == "allergies":
        if selected_pet.allergies:
            temp = json.loads(selected_pet.allergies)
            temp.pop(data['index'])
            selected_pet.allergies = json.dumps(temp)
    elif data['set'] == "medications":
        if selected_pet.medications:
            temp = json.loads(selected_pet.medications)
            temp.pop(data['index'])
            selected_pet.medications = json.dumps(temp)
    elif data['set'] == "vaccines":
        if selected_pet.vaccines:
            temp = json.loads(selected_pet.vaccines)
            temp.pop(data['index'])
            selected_pet.vaccines = json.dumps(temp)
            
        
    try:
        await db.commit()
        await db.refresh(selected_pet)
        return selected_pet
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return {
        'id': id,
        'data': data
    }
    

@router.post('/{id}/add/allergies')
async def update_my_pet_allergies(id: str, allergies: Allergies, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    pet_query = await db.execute(
            select(models.Pet).where(models.Pet.unique_id == id)
        )
    selected_pet:PetBaseSchema = pet_query.scalar_one_or_none()
    if not selected_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Pet not found')
    if selected_pet.owner_id != uuid.UUID(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not allowed to perform this action')
    if not selected_pet.allergies:
        selected_pet.allergies = json.dumps([allergies.dict()])
    else:
        temp = json.loads(selected_pet.allergies)
        temp.append(allergies.dict())
        selected_pet.allergies = json.dumps(temp)
        
    try:
        await db.commit()
        await db.refresh(selected_pet)
        return selected_pet
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.post('/{id}/add/medications')
async def update_my_pet_medications(id: str, medications: Medications, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    pet_query = await db.execute(
            select(models.Pet).where(models.Pet.unique_id == id)
        )
    selected_pet:PetBaseSchema = pet_query.scalar_one_or_none()
    if not selected_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Pet not found')
    if selected_pet.owner_id != uuid.UUID(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not allowed to perform this action')
    if not selected_pet.medications:
        selected_pet.medications = json.dumps([medications.dict()])
    else:
        temp = json.loads(selected_pet.medications)
        temp.append(medications.dict())
        selected_pet.medications = json.dumps(temp)
        
    try:
        await db.commit()
        await db.refresh(selected_pet)
        return selected_pet
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post('/{id}/add/vaccines')
async def update_my_pet_vaccines(id: str, vaccines: Vaccines, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    # Convert the string to a datetime object
    date_object = datetime.strptime(vaccines.date, "%Y-%m-%d")
    vaccines.date = date_object
    pet_query = await db.execute(
            select(models.Pet).where(models.Pet.unique_id == id)
        )
    selected_pet:PetBaseSchema = pet_query.scalar_one_or_none()
    
    if not selected_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Pet not found')
        
    if selected_pet.owner_id != uuid.UUID(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed to perform this action')
    
    if not selected_pet.vaccines:
        selected_pet.vaccines = json.dumps([vaccines.dict()], cls=CustomJSONEncoder)
    else:
        temp = json.loads(selected_pet.vaccines)
        # temp
        temp.append(vaccines.dict())
        selected_pet.vaccines = json.dumps(temp, cls=CustomJSONEncoder)
        
    try:
        await db.commit()
        await db.refresh(selected_pet)
        return selected_pet
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get('/{id}')
async def get_pet(id: str, db: Session = Depends(get_session)):
    response = await pet_repo.get_pet(id, db)
    return response

# @router.get('/owner/{id}/details')
@router.get('/owner/{id}/details', response_model=UserResponse)
async def get_owner_details(id: str, db: Session = Depends(get_session)):
    response = await pet_repo.get_owner_details(id, db)
    return response


@router.get('/{id}/get_details')
async def get_pet(id: str, db: Session = Depends(get_session)):
    response = await pet_repo.check_pet(id, db)
    return response


@router.get('/{id}/check')
async def get_pet(id: str, db: Session = Depends(get_session)):
    response = await pet_repo.check_pet(id, db)
    if response.owner_id is not None:
        data = {"has_owner": True}
    else:
        data = {"has_owner": False}
    return data

async def send_scan_email(user: models.User, email: List[str], link: str, coordinates: dict, pet: models.Pet):
    sample = await Email(user=user, url=link, email=email, coordinates=coordinates, pet=pet).sendScanNotificationEmail()
    return sample

async def create_notification(user: models.User, coordinates: dict, pet: models.Pet, db: Session):
    dt = { 'to': str(user.id), 
          'message': f"Someone scanned {pet.name}'s tag anonymously in <a style='color:blue;text-decoration-line: underline;'  href='https://www.google.com/maps?q={coordinates['latitude']},{coordinates['longitude']}&z=13&t=m' target='_blank'>this</a> location." }
    notif = NotificationBaseSchema(**dt)
    new_pet = models.Notification(**notif.dict())
    db.add(new_pet)
    await db.commit()
    await db.refresh(new_pet)
    return new_pet
    

@router.post('/scan/{id}')
async def get_pet(id: str, data: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_session)):
    response, user = await pet_repo.check_pet_with_user(id, db)
    if response.owner_id is not None:
        scan_data = {'qr_code_id': id}
        
        # url = f"{request.url.scheme}://{request.client.host}:{request.url.port}/api/v2/auth/verifyemail/{token.hex()}"
        # await Email(new_user, url, [payload.email]).sendVerificationCode()
        
        background_tasks.add_task(send_scan_email, user, [user.email], "facebook.com", data, response)
        background_tasks.add_task(create_notification, user, data, response, db)
        history = await scan_repo.save(ScanSchema(**scan_data).dict(), db)
        # get no of scans and set 0 if null    
        no_of_scans = 0 if response.no_of_scans is None else response.no_of_scans
        
        no_of_scans = no_of_scans + 1
        response.no_of_scans = no_of_scans
        response = await pet_repo.update_pet(id, response, db)
        
    return data

@router.get('/{id}/details')
async def get_pet(id: str, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    response = await pet_repo.get_my_pet(id, user_id, db)
    return response

@router.get('/{id}/notifications')
async def get_notifications(id: str, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    pet_query = await db.execute(
            select(models.Notification).where(models.Notification.to == id)
        )
    selected_pet = pet_query.scalars().all()
    if not selected_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Notification not found')
    return selected_pet

@router.get('/{id}/notifications/load')
async def get_notifications(id: str, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    pet_query = await db.execute(
            select(models.Notification).where(models.Notification.to == id).order_by(desc(models.Notification.created_at))
        )
    selected_pet = pet_query.scalars().all()
    if not selected_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Notification not found')
    return selected_pet

@router.get('/notifications/read')
async def get_notifications(background_tasks: BackgroundTasks, db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    try:
        background_tasks.add_task(pet_repo.read_notification, user_id, db)
        return "ok"
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Connection timed out')
        
@router.get('/unread/notifications/count')
async def get_unread_notifications_count(db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    # try:
        pet_query = await db.execute(
            select(models.Notification.id).where(models.Notification.to == user_id).where(models.Notification.is_read == False)
        )
        selected_pet = pet_query.scalars().all()
        return { 'count' : len(selected_pet) | 0}
    # except:
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                         detail=f'Connection timed out')


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
        box_size=30,
        border=4,
    )
    qr.add_data("https://secure-petz.info/"+str(data))
    qr.make(fit=True)

    # Generate QR code image
    img = qr.make_image(fill_color=(13,103,181), back_color=(255,255,255))
    # img = img.resize((1318, 1318))
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    return img_bytes

@router.post('/download-qr-image')
async def download_qr_image(data: dict, user_id: str = Depends(require_user)):
    try:
        img_bytes = generate_qr_code(data['unique_id']).getvalue()
        return Response(content=img_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/generate_qr_zip')
async def generate_qr_zip(data: list, user_id: str = Depends(require_user)):
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


@router.post('/generate-qr-all')
async def generate_qr_zip(db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    filtered_data = await pet_repo.get_all_pets(db)
    # return filtered_data
    # Create a ZIP file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        for item in filtered_data:
            # Generate QR code for each item and add it to the ZIP file
            qr_code_bytes = generate_qr_code(item)
            zip_file.writestr(f'qrcode_{item}.png', qr_code_bytes.read())
            
        csv_data = "\n".join([f"{x+1},https://secure-petz.info/{str(item)}" for x, item in enumerate(filtered_data)])
        zip_file.writestr('pets_data.csv', csv_data)

    # Move to the beginning of the ZIP buffer
    zip_buffer.seek(0)

    # Return the ZIP file as a response
    return StreamingResponse(zip_buffer, media_type="application/zip", headers={'Content-Disposition': 'attachment; filename=qr_codes.zip'})

    pet_query = await db.execute(
            select(models.Pet).where(models.Pet.unique_id == id)
        )
    selected_pet:PetBaseSchema = pet_query.scalar_one_or_none()
    if not selected_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Pet not found')
    if selected_pet.owner_id != uuid.UUID(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not allowed to perform this action')
    
    if not selected_pet.vaccines:
        selected_pet.vaccines = json.dumps([vaccines.dict()], cls=CustomJSONEncoder)
    else:
        temp = json.loads(selected_pet.vaccines, cls=CustomJSONEncoder)
        temp.append(vaccines.dict())
        selected_pet.vaccines = json.dumps(temp, cls=CustomJSONEncoder)
        
    try:
        await db.commit()
        await db.refresh(selected_pet)
        return selected_pet
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
    
    # selected_user.settings = settings
    
    # await db.commit()
    # await db.refresh(selected_user)
        
    return settings