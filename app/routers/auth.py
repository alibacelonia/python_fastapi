import base64
from datetime import timedelta
import datetime
import time
import hashlib
from random import randbytes
from fastapi import APIRouter, Request, Response, status, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import httpx
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
import requests

import aiohttp
import asyncio
from app.repositories import auth_repo

access_token_cache = {"token": None, "expires_at": None}
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
        
    # Check if the password is valid
    if not utils.verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Incorrect Email or Password')

    # Check if user verified his email
    if not user.verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Please verify your email address')


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

@router.post('/resend-email-verification')
async def resend_verificaiton_email(payload: dict, request: Request, db: Session = Depends(get_session)):
    try:
        email = payload['email']
        # Check if user already exist
        user_query = await db.execute(
            select(models.User)
            .where( models.User.email == EmailStr(email.lower()))
        )
        user: models.User = user_query.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='User account not found.')
        
        
            # Send Verification Email
        token = randbytes(10)
        hashedCode = hashlib.sha256()
        hashedCode.update(token)
        verification_code = hashedCode.hexdigest()
        # payload.firstname = verification_code
        user.verification_code = verification_code
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        await auth_repo.send_email_verification(db, request, token, user, email)
        
        return {"status_code": "200", "message": "Verification email successfully sent."}
    except Exception:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Cannot resend email verification. Please try again later.")


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


# Function to get the current time
def current_time():
    return datetime.datetime.utcnow()

# Function to check if the access token is expired
def is_token_expired():
    return access_token_cache["expires_at"] is None or current_time() >= access_token_cache["expires_at"]

# Function to fetch or refresh the access token
# Function to fetch or refresh the access token
async def get_or_refresh_access_token():
    # Check if the token is expired or not present
    if is_token_expired():
        try:
            # Base64 encode your username and password for Basic Authorization
            basic_auth = base64.b64encode(b'0oaxb9i8P9vQdXTsn3l5:0aBsGU3x1bc-UIF_vDBA2JzjpCPHjoCP7oI6jisp').decode('utf-8')

            # Set your API endpoint
            api_url = 'https://welcome.api2.sandbox.auspost.com.au/oauth/token'

            # Set the headers for Basic Authorization and form-urlencoded content type
            headers = {
                'Authorization': f'Basic {basic_auth}',
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            # Create an object with your parameters
            data = {
                'grant_type': 'client_credentials',
                'audience': 'https://api.payments.auspost.com.au',
            }

            # Convert the object to form-urlencoded format
            form_data = data

            # Make the HTTP request using httpx instead of axios
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, data=form_data, headers=headers)

            # Handle the response here
            if response.status_code == 200:
                # Update the cache with the new access token and expiration time
                access_token_cache["token"] = response.json().get("access_token")
                # Use expires_in from the response to set the expires_at in the cache
                expires_in = response.json().get("expires_in")
                access_token_cache["expires_at"] = current_time() + timedelta(seconds=expires_in)

            else:
                # Handle errors here
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Error: {response.text}")

        except Exception as e:
            # Handle other exceptions
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Error: {str(e)}") 

    # Return the access token from the cache
    return access_token_cache["token"]

async def make_payment_request(data):
    token = await get_or_refresh_access_token()
    url = "https://payments-stest.npe.auspost.zone/v2/payments"
    headers = {
        "Content-Type": "application/json",
        # "Idempotency-Key": "022361c6-3e59-40df-a58d-532bcc63c3ed",
        "Authorization": f"Bearer {token}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise HTTPException(status_code=response.status, detail=await response.text())


# Endpoint to get the securepay access token
@router.get("/securepay/get-access-token")
async def get_securepay_access_token():
    try:
        # Get or refresh the access token
        token = await get_or_refresh_access_token()

        # Return the token in the response
        return JSONResponse(content={"access_token": token}, status_code=200)

    except HTTPException as e:
        return e
    
@router.post("/securepay/make-payment")
async def get_headers(payload: dict, request: Request):
    headers = {
                'Content-Type': 'application/json'
                # 'Idempotency-Key': '022361c6-3e59-40df-a58d-532bcc63c3ed'
            }
    
    auth_header = request.headers.get('Authorization')
    if auth_header:
        headers['Authorization'] = auth_header
    else:
        raise HTTPException(status_code=401, detail="Authorization header is missing")
    
    # payload['amount'] = 1443
    
    api_url = 'https://payments-stest.npe.auspost.zone/v2/payments/'
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, json=payload, headers=headers)
        
    # return {'headers': headers}
    # return {'data': payload}
    return {"details": response.json()}
    
