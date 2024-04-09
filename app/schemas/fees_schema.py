from datetime import datetime
from typing import List
import uuid
from pydantic import BaseModel, EmailStr, constr
from app.schemas.user_schema import FilteredUserResponse


class FeeBaseSchema(BaseModel):
    
    fee_type: str
    display_name: str
    amount: float
    currency: str = "AUD"
    operation : str = "ADD"
    enabled: bool = True

    class Config:
        orm_mode = True


class CreateFeeSchema(FeeBaseSchema):
    created_at : datetime = None
    created_by : str = None
    
    class Config:
        orm_mode = True

class UpdateFeeSchema(FeeBaseSchema):
    updated_at : datetime
    updated_by : str
    
    class Config:
        orm_mode = True


class FeeResponse(FeeBaseSchema):
    created_at : datetime
    created_by : str
    updated_at : datetime
    updated_by : str
    
class FilteredFeeResponse(BaseModel):
    id: str
    display_name: str
    amount: float
    currency: str
    operation : str
    
    class Config:
        orm_mode = True



class ListFeeResponse(BaseModel):
    status: str
    results: int
    fees: List[FilteredFeeResponse]
