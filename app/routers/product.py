import json
from typing import List
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from app.email import Email

from ..schemas.product_schema import CreateProductSchema, DiscountSchema, FilteredProductResponse, ListProductResponse, ProductBaseSchema, ProductResponse, UpdateProductSchema
from ..database import get_session
from sqlalchemy.orm import Session
from .. import models, oauth2
from ..repositories import product_repo
import base64
import io
import boto3
from botocore.client import Config

router = APIRouter()

def convert_product_response_to_filtered(response: ProductResponse) -> FilteredProductResponse:
    return FilteredProductResponse(
        id=str(uuid.uuid4()),  # You might want to generate a unique ID for the filtered response
        description=response.description,
        price=response.price,
        currency=response.currency,
        category=response.category,
    )

@router.get('/')
async def get_pets(db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user), limit: int = 10, page: int = 1, search: str = '', filters: str = ''):
    response = await product_repo.get_products(db, limit, page, search, filters)
    return response

@router.get('/filtered')
async def get_pets(db: Session = Depends(get_session), limit: int = 10, page: int = 1, search: str = '', filters: str = ''):
    response = await product_repo.get_products(db, limit, page, search, filters, False)
    # response['products'] = [convert_product_response_to_filtered(item) for item in response['products']]
    return response


@router.post('/create')
async def get_all_products(product: CreateProductSchema, db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    # return product
    try:
        response = await product_repo.create_product(product, user_id, db)
        return response
    except HTTPException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Connection timed out.")

@router.post('/add-product')
async def add_products(
    product_name: str = Form(...),
    description: str = Form(...),
    price: str = Form(...),
    discount: str = Form(...),
    freebies: str = Form(...),
    category: str = Form(...),
    manufacturer: str = Form(...),
    enabled: bool = Form(...),
    files: List[UploadFile] = File(...), 
    db: Session = Depends(get_session), 
    user_id: str = Depends(oauth2.require_user)):
    
    data = CreateProductSchema(
        product_name=product_name,
        description=description,
        price=price,
        discount=DiscountSchema.parse_raw(discount),
        freebies=json.loads(freebies),
        category=category,
        manufacturer=manufacturer,
        enabled=enabled,
    )
    
    try:
        product = await product_repo.create_product(data, user_id, db)
    
    
        session = boto3.session.Session()
        client = session.client('s3',
                            region_name='syd1',
                            endpoint_url='https://syd1.digitaloceanspaces.com',
                            aws_access_key_id='DO00QX4YPL6NNLPW2L4G',
                            aws_secret_access_key='sBhMak3jCaEinYDMNQQYvElpiCsgv1DdegT8uBZDhf4')
        image_urls = []
        for file in files:
            contents = await file.read()
            contents_base64 = base64.b64encode(contents)
            contents_decoded = base64.b64decode(contents_base64)
            file_obj = io.BytesIO(contents_decoded)
            location = f"products/{product.product_id}/{file.filename}"
            client.upload_fileobj(file_obj, 'petnfc-storage', location, ExtraArgs={'ACL': 'public-read'})
            image_urls.append(f"https://petnfc-storage.syd1.cdn.digitaloceanspaces.com/{location}")
            
        product.image_urls = image_urls
        product.image_url = image_urls[0]
        
        
        updated_product = await product_repo.update_product(data, product.product_id, user_id, db)
        
        return updated_product
    except HTTPException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Connection timed out.")
    
    
@router.post('/update/{id}')
async def get_all_products(product: CreateProductSchema, id: str,  db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    try:
        response = await product_repo.update_product(product, id, user_id, db)
        return response
    except HTTPException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Connection timed out.")
    
@router.post('/delete/{id}')
async def delete_product(id: str, db: Session = Depends(get_session), user_id: str = Depends(oauth2.require_user)):
    response = await product_repo.delete_product(id, db)
    return response


@router.post('/get-buckets')
async def upload_files(files: List[UploadFile] = File(...)):
    session = boto3.session.Session()
    client = session.client('s3',
                        region_name='syd1',
                        endpoint_url='https://syd1.digitaloceanspaces.com',
                        aws_access_key_id='DO00QX4YPL6NNLPW2L4G',
                        aws_secret_access_key='sBhMak3jCaEinYDMNQQYvElpiCsgv1DdegT8uBZDhf4')
    response_data = []
    for file in files:
        contents = await file.read()
        contents_base64 = base64.b64encode(contents)
        contents_decoded = base64.b64decode(contents_base64)
        file_obj = io.BytesIO(contents_decoded)
        location = f"pets/{file.filename}"
        client.upload_fileobj(file_obj, 'petnfc-storage', location, ExtraArgs={'ACL': 'public-read'})
        response_data.append({"url": f"https://petnfc-storage.syd1.cdn.digitaloceanspaces.com/{location}"})
    return JSONResponse(content=response_data)

@router.post('/delete-buckets')
async def upload_files(request: Request):
    session = boto3.session.Session()
    client = session.client('s3',
                        region_name='syd1',
                        endpoint_url='https://syd1.digitaloceanspaces.com',
                        aws_access_key_id='DO00QX4YPL6NNLPW2L4G',
                        aws_secret_access_key='sBhMak3jCaEinYDMNQQYvElpiCsgv1DdegT8uBZDhf4')
    
    response = client.delete_object(Bucket='petnfc-storage', Key='pets/petnfc (1).png',)
    return response