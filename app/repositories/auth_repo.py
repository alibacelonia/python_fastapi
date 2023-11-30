from fastapi import APIRouter, Depends, HTTPException, Request, status
from psycopg2 import IntegrityError
from pydantic import EmailStr
from sqlalchemy import or_, select

from app import utils
from app.email import Email
from app.schemas.pet_schema import UpdatePetSchema

from ..schemas.user_schema import CreateUserSchema, UpdateUserSchema, UserResponse
from sqlalchemy.orm import Session
from .. import models

from random import randbytes
import hashlib


async def create_user(db: Session, request: Request, payload: CreateUserSchema):
    # try:    
    #     # Check if user already exist
    #     user_query = await db.execute(
    #         select(models.User)
    #         .where(models.User.email == EmailStr(payload.email.lower())
    #         )
    #     )
    #     user = user_query.scalar_one_or_none()
        
    #     if user:
    #         raise HTTPException(status_code=status.HTTP_409_CONFLICT,
    #                             detail='Account already exist')
    #     # Compare password and passwordConfirm
    #     if payload.password != payload.passwordConfirm:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST, detail='Passwords do not match')
    #     #  Hash the password
    #     payload.password = utils.hash_password(payload.password)
    #     del payload.passwordConfirm
    #     payload.email = EmailStr(payload.email.lower())
    #     new_user = models.User(**payload.dict())
    #     db.add(new_user)
    #     await db.commit()
    #     await db.refresh(new_user)
    #     return new_user
    # except TimeoutError:
    #     raise HTTPException(status_code=500, detail="Task timed out")
    # except IntegrityError as e:
    #     db.rollback()
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account already exist")
    # except Exception as e:
    #     db.rollback()
    #     raise HTTPException(status_code=status.WS_1011_INTERNAL_ERROR, detail=str(e))
    # Check if user already exist
    user_query = await db.execute(
    select(models.User)
    .where(
        or_(
            models.User.email == EmailStr(payload.email.lower()),
            models.User.phone_number == payload.phone_number
        )
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
    payload.role = 'user'
    payload.verified = False
    payload.email = EmailStr(payload.email.lower())
    
    
        # Send Verification Email
    token = randbytes(10)
    hashedCode = hashlib.sha256()
    hashedCode.update(token)
    verification_code = hashedCode.hexdigest()
    
    # payload.firstname = verification_code
    payload.verification_code = verification_code
    
    new_user = models.User(**payload.dict())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    try:
        url = f"{request.url.scheme}://{request.client.host}:{request.url.port}/api/v2/auth/verifyemail/{token.hex()}"
        await Email(new_user, url, [payload.email]).sendVerificationCode()
    except Exception as error:
        print('Error', error)
        new_user.verification_code = None
        await db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail='There was an error sending email')
    return new_user