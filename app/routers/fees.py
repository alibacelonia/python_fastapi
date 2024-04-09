import uuid
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from app.email import Email

from ..schemas.fees_schema import CreateFeeSchema, FilteredFeeResponse, ListFeeResponse, FeeBaseSchema, FeeResponse, UpdateFeeSchema
from ..database import get_session
from sqlalchemy.orm import Session
from .. import models, oauth2
from ..repositories import fees_repo

router = APIRouter()

def convert_fee_response_to_filtered(response: FeeResponse) -> FilteredFeeResponse:
    return FilteredFeeResponse(
        id=str(uuid.uuid4()),  # You might want to generate a unique ID for the filtered response
        display_name=response.display_name,
        amount=response.amount,
        currency=response.currency,
        operation=response.operation,
    )

@router.get('/')
async def get_pets(db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user), limit: int = 10, page: int = 1, search: str = '', filters: str = ''):
    response = await fees_repo.get_fees(db, limit, page, search, filters)
    return response

@router.get('/filtered')
async def get_pets(db: Session = Depends(get_session), limit: int = 10, page: int = 1, search: str = '', filters: str = ''):
    response = await fees_repo.get_fees(db, limit, page, search, filters, False)
    response['fees'] = [convert_fee_response_to_filtered(item) for item in response['fees']]
    return response


@router.post('/create')
async def get_all_fees(fee: CreateFeeSchema, db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    try:
        response = await fees_repo.create_fees(fee, user_id, db)
        return response
    except HTTPException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Connection timed out.")
    
    
@router.post('/update/{id}')
async def get_all_fees(fee: CreateFeeSchema, id: str,  db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    try:
        response = await fees_repo.update_fee(fee, id, user_id, db)
        return response
    except HTTPException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Connection timed out.")
    
@router.post('/delete/{id}')
async def delete_fee(id: str, db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    response = await fees_repo.delete_fee(id, db)
    return response
