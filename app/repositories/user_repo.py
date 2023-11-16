from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2 import IntegrityError
from pydantic import EmailStr
from sqlalchemy import or_, select

from app import utils

from ..schemas.user_schema import CreateUserSchema, UserResponse
from ..database import get_session
from sqlalchemy.orm import Session
from .. import models, oauth2

router = APIRouter()


async def get_user_details(user_id: str, db: Session):
    try:
        query = await db.execute(
            select(models.User).where(models.User.id == user_id)
        )
        user = query.scalar_one_or_none()
        return user
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