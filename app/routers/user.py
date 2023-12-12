from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.email import Email

from app.schemas.pet_schema import UpdatePetSchema
from app.user_encoder import UserEncoder

from ..schemas.user_schema import EmailSchema, PhoneSchema, UpdateUserSchema, UserResponse
from ..database import get_session
from sqlalchemy.orm import Session
from .. import models, oauth2
from ..repositories import user_repo
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from ..config import settings
import pyotp
import json
from ..utils import encrypt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
from base64 import b64encode
import os

router = APIRouter()

@router.get('/')
async def get_users(db: Session = Depends(get_session), limit: int = 10, page: int = 1, search: str = '', filters: str = '', user_id: str = Depends(oauth2.require_user)):
    response = await user_repo.get_users(db, limit, page, search, filters)
    return response

@router.get('/details')
async def get_me(db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    try:
        user = await user_repo.get_user_details(user_id, db)
        user_dict = user.to_dict()
        user_json = json.dumps(user_dict, default=str)
        
        backend = default_backend()
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=backend)
        key = kdf.derive(b"PetNFC1234")


        encrypted_data = encrypt(key, user_json)
        key_to_decrypt = b64encode(key).decode("utf-8")
        return {"data": encrypted_data, "key": key_to_decrypt}
    
    except HTTPException as e:
        return ({"status_code":status.HTTP_500_INTERNAL_SERVER_ERROR, "detail":"Timeout Error"})
    
@router.post('/check/email')
async def check_user(req: EmailSchema, db: Session = Depends(get_session)):
    response = await user_repo.check_email(req.email, db)
    return response


@router.post('/check/phone_number')
async def check_user(req: PhoneSchema, db: Session = Depends(get_session)):
    response = await user_repo.check_phone(req.phone, db)
    return response


@router.post('/update')
async def check_user(req: UpdateUserSchema, db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    user = await user_repo.update_user(req, db, user_id)
    return user

@router.post('/verify_phone_number')
async def check_user():
    response = await user_repo.send_sms()
    return response


@router.post('/send_email')
async def send_email():
    new_user = models.User(
        firstname='John',
        lastname='Doe',
        street_address='123 Main St',
        postal_code='12345',
        # Set other attributes as needed
        email='alibacelonia1234@gmail.com',
        password='securepassword'
    )

    try:
        url = f""
        await Email(new_user, url, [new_user.email]).sendVerificationCode()
    except Exception as error:
        print('Error', error)
        raise error
    return {'status': 'success', 'message': 'Verification token successfully sent to your email'}


@router.post('/send_otp')
async def generate_otp(email: str, db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    try:
        user = await user_repo.send_otp(db, user_id)
        await Email(user=user, email=[email], otp_code=user.otp).sendOTP()
        return {'detail': "OTP successfully sent", 'date': user.otp_created_at}
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot send OTP.")
    
    
@router.post('/verify_otp')
async def verify_otp(otp: str, db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    response = await user_repo.verify_otp(otp, db, user_id)
    return response

@router.get('/reset_otp')
async def reset_otp(db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    response = await user_repo.reset_otp(db, user_id)
    return response

@router.get('/get_remaining_time')
async def verify_otp(db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    response = await user_repo.get_remaining_time(db, user_id)
    return response