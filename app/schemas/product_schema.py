from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import json

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class DiscountSchema(BaseModel):
    type: str
    value: int
    expiration_date: datetime
    
    class Config:
        orm_mode = True

class ProductBaseSchema(BaseModel):
    product_name: str
    description: str = None
    price: float = 1
    currency: str = "AUD"
    discount: Optional[DiscountSchema] = None
    freebies: List[str] = []
    category: str = None
    manufacturer: str = None
    image_url: str = None
    image_urls: List[str] = []
    enabled: bool = True

    class Config:
        orm_mode = True


class CreateProductSchema(ProductBaseSchema):
    created_at : datetime = None
    created_by : str = None
    
    class Config:
        orm_mode = True

class UpdateProductSchema(ProductBaseSchema):
    updated_at : datetime
    updated_by : str
    
    class Config:
        orm_mode = True

class ProductResponse(ProductBaseSchema):
    created_at : datetime
    created_by : str
    updated_at : datetime
    updated_by : str
    
class FilteredProductResponse(ProductBaseSchema):
    
    class Config:
        orm_mode = True



class ListProductResponse(BaseModel):
    status: str
    results: int
    fees: List[FilteredProductResponse]
