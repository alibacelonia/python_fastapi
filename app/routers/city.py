from fastapi import APIRouter, Depends, Form, status, File, UploadFile
from app.database import get_session
# from app.schemas import Timezone, Translations, Country, State, City
from typing import Any, List, Optional
from app.repositories import city_repo

# from cachetools import TTLCache

# cache = TTLCache(maxsize=100, ttl=3600)

router = APIRouter()

# Get a list of pet types e.g. Dog, Cat, etc...
@router.get('/city')
async def get_all_cities():
    return city_repo.get_all_cities()

# Get a list of pet types e.g. Dog, Cat, etc...
@router.get('/city/{id}')
async def get_city_by_id(id: int):
    return city_repo.get_city_by_id(id)

@router.get('/country/{code}/city')
async def get_state_by_id(code: str):
    return city_repo.get_city_by_country_code(str(code).upper())

@router.get('/state/{code}/cities')
async def get_state_by_id(code: str):
    cities = city_repo.get_city_by_state_code(str(code).upper())
    transformed_states = [{"label": city['name'], "value": city['id']} for city in cities]
    return transformed_states

# @router.get('/country/{country_code}/state/{state_code}/city')
# async def get_state_by_id(country_code: str, state_code: str):
#     return city_repo.get_state_by_state_code(country_code, state_code)

# Get a list of pet types e.g. Dog, Cat, etc...
@router.get('/city/search/{name}')
async def get_city_by_name(name: str):
    return city_repo.search_city(name)