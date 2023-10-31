from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.config import settings
from app.database import init_db
from app.routers import user, auth, post, pets


from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from fastapi.staticfiles import StaticFiles
# from aiofiles import open as async_open
import os, json

app = FastAPI()



# app.mount("/files", StaticFiles(directory="app/files"), name="files")
app.mount("/userdata", StaticFiles(directory="app/userdata"), name="userdata")

class BaseResponseModel(BaseModel):
    status_code: int
    detail: str
    
    
# @app.exception_handler(StarletteHTTPException)
# def http_exception_handler(request: Request, exc):
#     error_response = BaseResponseModel(
#         status_code=exc.status_code,
#         detail=exc.detail
#     )
#     return JSONResponse(status_code=exc.status_code, content=error_response.dict())

# @app.exception_handler(RequestValidationError)
# def validation_exception_handler(request: Request, exc: RequestValidationError):
#     response_data = BaseResponseModel(
#         status_code=400,
#         detail="Invalid request"
#     )
#     return JSONResponse(status_code=400, content=response_data.dict())

origins = [
    settings.CLIENT_ORIGIN,
    "http://192.168.1.3:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, tags=['Auth'], prefix='/api/v2/auth')
app.include_router(user.router, tags=['Users'], prefix='/api/v2/user')
app.include_router(pets.router, tags=['Pets'], prefix='/api/v2/pet')
app.include_router(post.router, tags=['Posts'], prefix='/api/v2/post')


@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get('/api/v2')
def root():
    return {'message': 'Hello World'}
