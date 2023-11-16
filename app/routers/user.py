from fastapi import APIRouter, Depends, HTTPException, status

from ..schemas.user_schema import EmailSchema, PhoneSchema, UserResponse
from ..database import get_session
from sqlalchemy.orm import Session
from .. import models, oauth2
from ..repositories import user_repo

router = APIRouter()


@router.get('/details', response_model=UserResponse)
async def get_me(db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    try:
        user = await user_repo.get_user_details(user_id, db)
        return user
    except HTTPException as e:
        return ({"status_code":status.HTTP_500_INTERNAL_SERVER_ERROR, "detail":"Timeout Error"})
    
@router.post('/check/email')
async def check_user(req: EmailSchema, db: Session = Depends(get_session)):
    user = await user_repo.check_email(req.email, db)
    return user


@router.post('/check/phone_number')
async def check_user(req: PhoneSchema, db: Session = Depends(get_session)):
    user = await user_repo.check_phone(req.phone, db)
    return user
