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
from datetime import datetime, timedelta
import pytz
import secrets


router = APIRouter()

async def get_users(db: Session):
    try:
        query = await db.execute(
            select(models.User).where(models.User.role == "user")
        )
        users: models.User = query.scalars().all()
        
        return users
    
    except TimeoutError:
        raise HTTPException(status_code=500, detail="Task timed out")
    
async def get_pets(db: Session):
    try:
        query = await db.execute(
            select(models.Pet)
        )
        pets: models.Pet = query.scalars().all()
        
        return pets
    
    except TimeoutError:
        raise HTTPException(status_code=500, detail="Task timed out")
    
async def get_feedbacks(db: Session):
    try:
        query = await db.execute(
            select(models.Feedback)
        )
        pets: models.Pet = query.scalars().all()
        
        return pets
    
    except TimeoutError:
        raise HTTPException(status_code=500, detail="Task timed out")
