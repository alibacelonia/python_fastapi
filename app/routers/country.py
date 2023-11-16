from fastapi import APIRouter, Depends, Form, status, File, UploadFile
from fastapi.datastructures import FormData
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session
from app.database import get_session
# from app.schemas import Timezone, Translations, Country, State, City
from typing import Any, List, Optional
from app.repositories import country_repo
from fastapi.staticfiles import StaticFiles
import json
import httpx
import os

# from cachetools import TTLCache

# cache = TTLCache(maxsize=100, ttl=3600)

router = APIRouter()

# Get a list of pet types e.g. Dog, Cat, etc...
@router.get('/')
async def get_all_countries():
    return country_repo.get_all_countries()

# Get a list of pet types e.g. Dog, Cat, etc...
@router.get('/{id}')
async def get_country_by_id(id: int):
    return country_repo.get_country_by_id(id)

# Get a list of pet types e.g. Dog, Cat, etc...
@router.get('/search/{name}')
async def get_country_by_name(name: str):
    return country_repo.search_country(name)