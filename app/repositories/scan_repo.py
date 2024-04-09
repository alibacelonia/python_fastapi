from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.scan_schema import ScanSchema

from ..database import get_session
from sqlalchemy.orm import Session
from .. import models


router = APIRouter()

async def save(data: ScanSchema, db: Session):
    try:
        new_pet = models.ScanHistory(**data)
        db.add(new_pet)
        await db.commit()
        await db.refresh(new_pet)
        return new_pet
    
    except TimeoutError:
        raise HTTPException(status_code=500, detail="Task timed out")