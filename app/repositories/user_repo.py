from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from psycopg2 import IntegrityError
from pydantic import EmailStr
from sqlalchemy import Column, DateTime, MetaData, String, Table, and_, delete, func, or_, select

from app import utils
from app.email import Email
from app.schemas.pet_schema import UpdatePetSchema

from ..schemas.user_schema import CreateUserSchema, UpdateUserSchema, UserResponse
from ..database import get_session
from sqlalchemy.orm import Session
from .. import models, oauth2
from ..config import settings
import pyotp
from twilio.rest import Client
from datetime import datetime, timedelta
import pytz
import secrets


router = APIRouter()


australia_timezone = pytz.timezone('Australia/Sydney')
philippines_timezone = pytz.timezone('Asia/Manila')

async def create_reset_token(db, email: str):
    # Generate a unique token
    token = secrets.token_urlsafe(32)

    # Set expiration time (e.g., 1 hour from now)
    expiration_time = datetime.utcnow() + timedelta(minutes=10)

    # Store the token in the database
    # query = models.ResetToken.insert().values(token=token, email=email, expires_at=expiration_time)
    reset_token = models.ResetToken(token=token, email=email, expires_at=expiration_time)
    db.add(reset_token)
    await db.commit()
    await db.refresh(reset_token)
    return token
    
async def confirm_password_reset(db: Session, reset_token: str, new_password: str):
    # Check if the reset token exists and is not expired
    # reset_token_obj = db.query(models.ResetToken).filter_by(token=reset_token).first()
    
    token_result = await db.execute(select(models.ResetToken).filter_by(token=reset_token).order_by(models.ResetToken.expires_at.desc()))
    reset_token_obj = token_result.scalar_one_or_none()

    if not reset_token_obj or reset_token_obj.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    # Reset the password (update it in the database or authentication system)
    # user = db.query(models.User).filter_by(email=reset_token_obj.email).first()
    user_result = await db.execute(select(models.User).filter_by(email=reset_token_obj.email))
    user = user_result.scalar_one_or_none()

    if user:
        # Update the user's password (replace this with your actual password update logic)
        user.password = utils.hash_password(new_password)

        # Remove the reset token from the database
        # db.delete(reset_token_obj)

        # Commit the changes to the database
        await db.execute(delete(models.ResetToken).where(models.ResetToken.email == user.email))
        await db.commit()

        return {"message": "Password reset successful"}

    raise HTTPException(status_code=404, detail="User not found")

async def get_users(db: Session, limit: int, page: int, search: str = '', filters: str = ''):
    skip = (page - 1) * limit
    
    search_condition = (
        or_(
            or_(
                and_(
                    models.User.firstname.is_(None),  # NULL values
                    search == "",  # Empty search term
                ),
                and_(
                    models.User.lastname.is_(None),  # NULL values
                    search == "",  # Empty search term
                )
            ),
            models.User.firstname.ilike(f"%{search}%"),  # Non-empty names matching the search term
            models.User.lastname.ilike(f"%{search}%"),  # Non-empty names matching the search term
        )
    )
    
    filter_items = filters.split(',') if filters else []
    for item in filter_items:
        if len(item.split('=')) >= 2:
            key, value = item.split('=')
            if key and value:
                if key == 'status':
                    if value.lower() == "active":
                        search_condition = and_(search_condition, models.User.status == 'active')
                    elif value.lower() == "deactivated":
                        search_condition = and_(search_condition, models.User.status == 'deactivated')
                
                if key == 'email':
                    if value.lower() == "verified":
                        search_condition = and_(search_condition, models.User.verified == True)
                    elif value.lower() == "not-verified":
                        search_condition = and_(search_condition, models.User.verified == False)


    total_items = await db.scalar(
        select(func.count())
        .select_from(models.User)
        .where(models.User.role == 'user')
        .filter(search_condition)
    )
    
    total_pages = -(-total_items // limit)
    
    query = await db.execute(
            select(models.User)
            .where(models.User.role == 'user')
            .filter(search_condition)
            .group_by(models.User.id)
            .order_by(models.User.id.asc())  # Order by id
            .limit(limit)
            .offset(skip)
        )
    users: List[models.User] = query.scalars().all()
    
    user_responses = [UserResponse(**user.to_dict()) for user in users]
    
    return {'status': 'success', 'results': len(users), 'total_pages': total_pages, 'total_items':total_items, 'users': user_responses}


async def get_user_details(user_id: str, db: Session):
    try:
        query = await db.execute(
            select(models.User).where(models.User.id == user_id)
        )
        user: models.User = query.scalar_one_or_none()
        
        user_response = UserResponse(
            id=user.id,
            firstname=user.firstname,
            lastname=user.lastname,
            street_address=user.street_address,
            postal_code=user.postal_code,
            city_code=user.city_code,
            city=user.city,
            state_code=user.state_code,
            state=user.state,
            country_code=user.country_code,
            country=user.country,
            phone_number=user.phone_number,
            photo=user.photo,
            secondary_contact=user.secondary_contact,
            secondary_contact_number=user.secondary_contact_number,
            verified=user.verified,
            verification_code=user.verification_code,
            otp=user.otp,
            otp_secret=user.otp_secret,
            otp_created_at=user.otp_created_at,
            role=user.role,
            email=user.email,
            password=user.password,
            created_at=user.created_at,
            updated_at=user.updated_at,
            settings=user.settings
        )
        return user_response
    
    except TimeoutError:
        raise HTTPException(status_code=500, detail="Task timed out")

async def check_email(email: str, db: Session):
    try:
        query = await db.execute(
            select(models.User).where(models.User.email == email)
        )
        user = query.scalar_one_or_none()
        
        if user:
                raise HTTPException(status_code=409,
                                    detail='Email is already in use.')
        return {'details' : 'OK'}
    
    except TimeoutError:
        raise HTTPException(status_code=500, detail="Task timed out")

async def check_email_for_pwreset(email: str, db: Session):
    try:
        query = await db.execute(
            select(models.User).where(models.User.email == email)
        )
        user = query.scalar_one_or_none()
        
        if not user:
                raise HTTPException(status_code=404,
                                    detail='Email not found.')
        return user
    
    except TimeoutError:
        raise HTTPException(status_code=500, detail="Task timed out")

async def check_phone(phone: str, db: Session):
    try:
        query = await db.execute(
            select(models.User).where(models.User.phone_number == phone)
        )
        user = query.scalar_one_or_none()
        
        if user:
                raise HTTPException(status_code=409,
                                    detail='Phone Number is already in use.')
        return {'details' : 'OK'}
    
    except TimeoutError:
        raise HTTPException(status_code=500, detail="Task timed out")

async def add_user(db: Session, payload: CreateUserSchema):
    try:    
        # Check if user already exist
        # user_query = db.query(models.User).filter(
        #     models.User.email == EmailStr(payload.email.lower()))
        # user = user_query.first()
        
        user_query = await db.execute(
            select(models.User)
            .where(models.User.email == EmailStr(payload.email.lower())
            )
        )
        user = user_query.scalar_one_or_none()
        
        if user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail='Account already exist')
        # Compare password and passwordConfirm
        if payload.password != payload.passwordConfirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Passwords do not match')
        #  Hash the password
        payload.password = utils.hash_password(payload.password)
        del payload.passwordConfirm
        payload.email = EmailStr(payload.email.lower())
        new_user = models.User(**payload.dict())
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except TimeoutError:
        raise HTTPException(status_code=500, detail="Task timed out")
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account already exist")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.WS_1011_INTERNAL_ERROR, detail=str(e))
    
# update user with authentication
async def update_user(user: UpdateUserSchema, db: Session, user_id: str):
    
    pet_query = await db.execute(
            select(models.User).where(models.User.id == user_id)
        )
    updated_user:UserResponse = pet_query.scalar_one_or_none()

    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'User not found')
        
    if updated_user is not None:
            for key, value in user.dict(exclude_unset=True).items():
                setattr(updated_user, key, value)
                
            if user.email is not None:
                setattr(updated_user, 'otp', None)
                setattr(updated_user, 'otp_secret', None)
                setattr(updated_user, 'otp_created_at', None)
                
            await db.commit()
    return updated_user

async def send_sms():
    account_sid = settings.TWILIO_ACCOUNT_SSID
    auth_token = settings.TWILIO_AUTH_TOKEN
    client = Client(account_sid, auth_token)

    message = client.messages \
                    .create(
                        body="Join Earth's mightiest heroes. Like Kevin Bacon.",
                        from_='+12674634768',
                        to='+639616398508'
                 )
    return message.sid

async def send_otp(db: Session, user_id: str):
    query = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = query.scalar_one_or_none()
    
    if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail='You are not authenticated')
    if user.otp_secret is None:
        user.otp_secret = pyotp.random_base32()
        
    totp = pyotp.TOTP(user.otp_secret, interval=600)
    user.otp = totp.now() 
    current_utc_time = datetime.utcnow()
    new_utc_time = current_utc_time + timedelta(minutes=5, seconds=5)
    user.otp_created_at = new_utc_time.replace(tzinfo=pytz.utc).astimezone(philippines_timezone)
    await db.commit()
    await db.refresh(user)
    return user
    
async def verify_otp(otp_code: str, db: Session, user_id: str):
    try:
        query = await db.execute(
            select(models.User).where(models.User.id == user_id)
        )
        user: models.User = query.scalar_one_or_none()
        
        if not user:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail='You are not authenticated')
            
        
        totp = pyotp.TOTP(user.otp_secret, interval=600)
        result = totp.verify(otp_code)
        return { 'isValid' : result}
        
    except TimeoutError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Task timed out")
    
async def reset_otp(db: Session, user_id: str):
    try:
        query = await db.execute(
            select(models.User).where(models.User.id == user_id)
        )
        user: models.User = query.scalar_one_or_none()
        
        if not user:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail='You are not authenticated')
            
            
        
        user.otp = None
        user.otp_secret = None
        user.otp_created_at = None
        
        await db.commit()
        
        user_response = UserResponse(
            id=user.id,
            firstname=user.firstname,
            lastname=user.lastname,
            street_address=user.street_address,
            postal_code=user.postal_code,
            city_code=user.city_code,
            city=user.city,
            state_code=user.state_code,
            state=user.state,
            country_code=user.country_code,
            country=user.country,
            phone_number=user.phone_number,
            photo=user.photo,
            secondary_contact=user.secondary_contact,
            secondary_contact_number=user.secondary_contact_number,
            verified=user.verified,
            verification_code=user.verification_code,
            otp=None,
            otp_secret=None,
            otp_created_at=None,
            role=user.role,
            email=user.email,
            password=user.password,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        return user_response
        
    except TimeoutError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Task timed out")
    
async def get_remaining_time(db: Session, user_id: str):
    try:
        query = await db.execute(
            select(models.User).where(models.User.id == user_id)
        )
        user: models.User = query.scalar_one_or_none()
        
        if not user:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail='You are not authenticated')
            
        
        totp = pyotp.TOTP(user.otp_secret)
        
        return { 'time_remaining' : totp.interval - datetime.now().timestamp() % totp.interval}
        
    except TimeoutError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Task timed out")
    
