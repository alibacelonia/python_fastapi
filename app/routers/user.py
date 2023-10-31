from fastapi import APIRouter, Depends

from ..schemas.user_schema import UserResponse
from ..database import get_session
from sqlalchemy.orm import Session
from .. import models, oauth2
from ..repositories import user_repo

router = APIRouter()


@router.get('/details', response_model=UserResponse)
async def get_me(db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    return await user_repo.get_user_details(user_id, db)
