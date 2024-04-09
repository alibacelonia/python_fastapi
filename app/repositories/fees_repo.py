import os
from pathlib import Path
import shutil
from typing import List
import uuid

from pydantic import EmailStr
from sqlalchemy import and_, func, or_, select, update

from app import utils
from app.email import Email
from app.schemas.user_schema import CreateUserSchema, FilteredUserResponse
from .. import models
from ..schemas.fees_schema import FeeBaseSchema, FeeResponse, FilteredFeeResponse, ListFeeResponse, CreateFeeSchema, UpdateFeeSchema
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, UploadFile, status, APIRouter, Response
from ..database import get_session
from app.oauth2 import require_user
from ..repositories import user_repo

router = APIRouter()


USERDATA_DIR = os.path.join("app", "userdata")

CURRENCY_CODES = [currency["Code"].upper() for currency in utils.get_currency()]

# get fees with authentication
async def get_fees(db: Session, limit: int, page: int, search: str = '', filters: str = '', show_all: bool = True):
    skip = (page - 1) * limit
    
    search_condition = (
        or_(
            or_(
                and_(
                    models.Fee.display_name.is_(None),  # NULL values
                    search == "",  # Empty search term
                ),
                and_(
                    models.Fee.fee_type.is_(None),  # NULL values
                    search == "",  # Empty search term
                )
            ),
            models.Fee.display_name.ilike(f"%{search}%"),  # Non-empty names matching the search term
            models.Fee.fee_type.ilike(f"%{search}%"),  # Non-empty names matching the search term
        )
    )
    
    filter_items = filters.split(',') if filters else []
    for item in filter_items:
        if len(item.split('=')) >= 2:
            key, value = item.split('=')
            if key and value:
                if key == 'operation':
                    if value.upper() in ["ADD", "SUB", "MUL", "DIV"]:
                        search_condition = and_(search_condition, models.Fee.operation == value.upper())
                
                elif key == 'currency':
                    if value.upper() in CURRENCY_CODES:
                        search_condition = and_(search_condition, models.Fee.currency == value.upper())

    total_items_query = (
        select(func.count())
        .select_from(models.Fee)
        .filter(search_condition)
    )

    if not show_all:
        total_items_query = total_items_query.where(models.Fee.enabled == True)

    total_items = await db.scalar(total_items_query)
    
    total_pages = -(-total_items // limit)
    
    common_query = (
        select(models.Fee)
        .filter(search_condition)
        .group_by(models.Fee.id)
        .order_by(models.Fee.created_at.desc())  # Order by id
        .limit(limit)
        .offset(skip)
    )

    if not show_all:
        common_query = common_query.where(models.Fee.enabled == True)

    query = await db.execute(common_query)
    fees = query.scalars().all()
    
    return {'status': 'success', 'results': len(fees), 'total_pages': total_pages, 'total_items':total_items, 'fees': fees}

# create fees without authentication
async def create_fees(fees: CreateFeeSchema, user_id: str, db: Session):
    fees.created_by = user_id
    new_fees = models.Fee(**fees.dict())
    db.add(new_fees)
    await db.commit()
    await db.refresh(new_fees)
    return new_fees

async def update_fee(fee: UpdateFeeSchema, id: str, user_id: str, db: Session):
    fee_query = await db.execute(
            select(models.Fee).where(models.Fee.id == id)
        )
    selected_fee = fee_query.scalar_one_or_none()
    if not selected_fee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Fee not found')
        
    if selected_fee is not None:
            for key, value in fee.dict(exclude_unset=True).items():
                setattr(selected_fee, key, value)
            await db.commit()
    return selected_fee

async def delete_fee(id: str, db: Session):
    fee = await db.get(models.Fee, id)
    if fee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee not found.")

    # Delete the fee
    await db.delete(fee)
    await db.commit()
    
    return {"status_code": "200", "message": "Fee deleted successfully."}