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
from ..schemas.product_schema import ProductBaseSchema, ProductResponse, FilteredProductResponse, ListProductResponse, CreateProductSchema, UpdateProductSchema
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, UploadFile, status, APIRouter, Response
from ..database import get_session
from app.oauth2 import require_user
from ..repositories import user_repo
import json
from datetime import datetime

router = APIRouter()


USERDATA_DIR = os.path.join("app", "userdata")

CURRENCY_CODES = [currency["Code"].upper() for currency in utils.get_currency()]


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# get products with authentication
async def get_products(db: Session, limit: int, page: int, search: str = '', filters: str = '', show_all: bool = True):
    skip = (page - 1) * limit
    
    search_condition = (
        or_(
            or_(
                and_(
                    models.Product.product_name.is_(None),  # NULL values
                    search == "",  # Empty search term
                ),
                and_(
                    models.Product.description.is_(None),  # NULL values
                    search == "",  # Empty search term
                )
            ),
            models.Product.product_name.ilike(f"%{search}%"),  # Non-empty names matching the search term
            models.Product.description.ilike(f"%{search}%"),  # Non-empty names matching the search term
        )
    )
    
    filter_items = filters.split(',') if filters else []
    for item in filter_items:
        if len(item.split('=')) >= 2:
            key, value = item.split('=')
            if key and value:
                if key == 'enabled':
                    if value:
                        search_condition = and_(search_condition, models.Product.enabled)

    total_items_query = (
        select(func.count())
        .select_from(models.Product)
        .filter(search_condition)
    )

    if not show_all:
        total_items_query = total_items_query.where(models.Product.enabled == True)

    total_items = await db.scalar(total_items_query)
    
    total_pages = -(-total_items // limit)
    
    common_query = (
        select(models.Product)
        .filter(search_condition)
        .group_by(models.Product.product_id)
        .order_by(models.Product.created_at.desc())  # Order by id
        .limit(limit)
        .offset(skip)
    )

    if not show_all:
        common_query = common_query.where(models.Product.enabled == True)

    query = await db.execute(common_query)
    products = query.scalars().all()
    
    return {'status': 'success', 'results': len(products), 'total_pages': total_pages, 'total_items':total_items, 'products': products}

# create products without authentication
async def create_product(product: CreateProductSchema, user_id: str, db: Session):
    product.created_by = user_id
    product.discount.expiration_date = product.discount.expiration_date.isoformat()
    # discount = product.discount
    
    new_products = models.Product(**product.dict())
    # return new_products
    db.add(new_products)
    await db.commit()
    await db.refresh(new_products)
    return new_products

async def update_product(product: UpdateProductSchema, id: str, user_id: str, db: Session):
    product_query = await db.execute(
            select(models.Product).where(models.Product.product_id == id)
        )
    selected_product = product_query.scalar_one_or_none()
    if not selected_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Product not found')
        
    if selected_product is not None:
            for key, value in product.dict(exclude_unset=True).items():
                setattr(selected_product, key, value)
            await db.commit()
    return selected_product

async def delete_product(id: str, db: Session):
    product = await db.get(models.Product, id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    # Delete the product
    await db.delete(product)
    await db.commit()
    
    return {"status_code": "200", "message": "Product deleted successfully."}