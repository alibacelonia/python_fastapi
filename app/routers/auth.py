from datetime import timedelta
import hashlib
from random import randbytes
from fastapi import APIRouter, Request, Response, status, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy import or_, select

from app import oauth2
from ..schemas.user_schema import CreateUserSchema, LoginUserSchema, UserBaseSchema
from .. import models, utils
from sqlalchemy.orm import Session
from ..database import get_session
from app.oauth2 import AuthJWT
from ..config import settings
from ..email import Email


router = APIRouter()
ACCESS_TOKEN_EXPIRES_IN = settings.ACCESS_TOKEN_EXPIRES_IN
REFRESH_TOKEN_EXPIRES_IN = settings.REFRESH_TOKEN_EXPIRES_IN


@router.post('/register', status_code=status.HTTP_201_CREATED)
async def create_user(payload: CreateUserSchema, request: Request, db: Session = Depends(get_session)):
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
    payload.verified = True
    payload.email = EmailStr(payload.email.lower())
    
    
        # Send Verification Email
    token = randbytes(10)
    hashedCode = hashlib.sha256()
    hashedCode.update(token)
    verification_code = hashedCode.hexdigest()
    
    payload.firstname = verification_code
    payload.verification_code = verification_code
    
    new_user = models.User(**payload.dict())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    try:
        url = f"{request.url.scheme}://{request.client.host}:{request.url.port}/api/auth/verifyemail/{token.hex()}"
        await Email(new_user, url, [payload.email]).sendVerificationCode()
    except Exception as error:
        print('Error', error)
        new_user.verification_code = None
        await db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail='There was an error sending email')
    return {'status': 'success', 'message': 'Verification token successfully sent to your email'}


@router.post('/login')
async def login(payload: LoginUserSchema, response: Response, db: Session = Depends(get_session), Authorize: AuthJWT = Depends()):
    # Check if the user exist
    query = await db.execute(select(models.User).where(models.User.email == EmailStr(payload.email.lower())))
    user = query.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Incorrect Email or Password')

    # Check if user verified his email
    if not user.verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Please verify your email address')

    # Check if the password is valid
    if not utils.verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Incorrect Email or Password')

    # Create access token
    access_token = Authorize.create_access_token(
        subject=str(user.id), expires_time=timedelta(minutes=ACCESS_TOKEN_EXPIRES_IN))

    # Create refresh token
    refresh_token = Authorize.create_refresh_token(
        subject=str(user.id), expires_time=timedelta(minutes=REFRESH_TOKEN_EXPIRES_IN))

    # Store refresh and access tokens in cookie
    response.set_cookie('access_token', access_token, ACCESS_TOKEN_EXPIRES_IN * 60,
                        ACCESS_TOKEN_EXPIRES_IN * 60, '/', None, False, True, 'lax')
    response.set_cookie('refresh_token', refresh_token,
                        REFRESH_TOKEN_EXPIRES_IN * 60, REFRESH_TOKEN_EXPIRES_IN * 60, '/', None, False, True, 'lax')
    response.set_cookie('logged_in', 'True', ACCESS_TOKEN_EXPIRES_IN * 60,
                        ACCESS_TOKEN_EXPIRES_IN * 60, '/', None, False, False, 'lax')

    # Send both access
    return {'status': 'success', 'access_token': access_token}


@router.get('/refresh')
async def refresh_token(response: Response, request: Request, Authorize: AuthJWT = Depends(), db: Session = Depends(get_session)):
    try:
        Authorize.jwt_refresh_token_required()

        user_id = Authorize.get_jwt_subject()
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not refresh access token')
        
        query = await db.execute(select(models.User).where(models.User.id == user_id))
        user = query.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='The user belonging to this token no logger exist')
        access_token = Authorize.create_access_token(
            subject=str(user.id), expires_time=timedelta(minutes=ACCESS_TOKEN_EXPIRES_IN))
    except Exception as e:
        error = e.__class__.__name__
        if error == 'MissingTokenError':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Please provide refresh token')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    response.set_cookie('access_token', access_token, ACCESS_TOKEN_EXPIRES_IN * 60,
                        ACCESS_TOKEN_EXPIRES_IN * 60, '/', None, False, True, 'lax')
    response.set_cookie('logged_in', 'True', ACCESS_TOKEN_EXPIRES_IN * 60,
                        ACCESS_TOKEN_EXPIRES_IN * 60, '/', None, False, False, 'lax')
    return {'access_token': access_token}


@router.get('/logout', status_code=status.HTTP_200_OK)
async def logout(response: Response, Authorize: AuthJWT = Depends(), user_id: str = Depends(oauth2.require_user)):
    Authorize.unset_jwt_cookies()
    response.set_cookie('logged_in', '', -1)

    return {'status': 'success'}


@router.get('/verifyemail/{token}')
async def verify_me(token: str, db: Session = Depends(get_session)):
    hashedCode = hashlib.sha256()
    hashedCode.update(bytes.fromhex(token))
    verification_code = hashedCode.hexdigest()
    user_query = db.query(models.User).filter(
        models.User.verification_code == verification_code)
    db.commit()
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='Email can only be verified once')
    user_query.update(
        {'verified': True, 'verification_code': None}, synchronize_session=False)
    db.commit()
    return {
        "status": "success",
        "message": "Account verified successfully"
    }
