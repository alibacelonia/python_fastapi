from datetime import timedelta
import hashlib
from random import randbytes
from fastapi import APIRouter, Request, Response, status, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from sqlalchemy import or_, select

from app import oauth2
from ..schemas.user_schema import ChangePasswordUserSchema, CreateUserSchema, LoginUserSchema, UserBaseSchema
from .. import models, utils
from sqlalchemy.orm import Session
from ..database import get_session
from app.oauth2 import AuthJWT
from ..config import settings
from ..email import Email


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
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
    user = user_query.first()
    
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
    return {'status': 'success', 'access_token': access_token, 'role': user.role}


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
    return {'access_token': access_token, 'role': user.role}


@router.get('/logout', status_code=status.HTTP_200_OK)
async def logout(response: Response, Authorize: AuthJWT = Depends(), user_id: str = Depends(oauth2.require_user)):
    Authorize.unset_jwt_cookies()
    response.set_cookie('logged_in', '', -1)

    return {'status': 'success'}


@router.get('/verifyemail/{token}')
async def verify_me(token: str, request: Request, db: Session = Depends(get_session)):
    hashedCode = hashlib.sha256()
    hashedCode.update(bytes.fromhex(token))
    verification_code = hashedCode.hexdigest()
    
    query = await db.execute(select(models.User).where(
        models.User.verification_code == verification_code))
    user = query.scalar_one_or_none()
    if not user:
        # raise HTTPException(
        #     status_code=status.HTTP_403_FORBIDDEN, detail='Email can only be verified once')
        return templates.TemplateResponse("already_verified.html",{"request": request})
        
    user.verification_code = verification_code
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    user.verification_code = None
    user.verified = True
    
    db.add(user)
    await db.commit()
    return templates.TemplateResponse("success_verification.html",{"request": request})


# @router.get('/otp/{id}')
# async def send_otp(request: Request, response_class=HTMLResponse):
#     return templates.TemplateResponse("success_verification.html",{"request": request})

@router.post('/change_password')
async def login(payload: ChangePasswordUserSchema, db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    # Check if the user exist
    query = await db.execute(select(models.User).where(models.User.id == user_id))
    user: models.User = query.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not authenticated')

    # Check if the password is valid
    if not utils.verify_password(payload.current_password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Incorrect Password')
        
    # Compare password and passwordConfirm
    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Passwords do not match')
    #  Hash the password
    user.password = utils.hash_password(payload.new_password)
    
    
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {'status': 'success'}
    except:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Passwords do not match')

    