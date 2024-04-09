from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from app.email import Email

from ..database import get_session
from sqlalchemy.orm import Session
from .. import models, oauth2

router = APIRouter()


@router.get('/')
async def get_scan_history(db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    query = await db.execute(
            select(models.ScanHistory)
        )
    pets = query.scalars().all()
    return pets
