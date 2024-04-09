from uuid import UUID
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app import models
from app.config import settings
from app.database import init_db
from app.routers import user, auth, post, pets, city, country, state, feedback, fees, product, dashboard, scan


from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from fastapi.staticfiles import StaticFiles
# from aiofiles import open as async_open
import os, json
from sqlalchemy import event

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
    "http://localhost:4001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    # allow_methods=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


app.include_router(auth.router, tags=['Auth'], prefix='/api/v2/auth')
app.include_router(user.router, tags=['Users'], prefix='/api/v2/user')
app.include_router(pets.router, tags=['Pets'], prefix='/api/v2/pet')
app.include_router(fees.router, tags=['Fee'], prefix='/api/v2/fees')
app.include_router(feedback.router, tags=['Feedbacks'], prefix='/api/v2/feedback')
app.include_router(post.router, tags=['Posts'], prefix='/api/v2/post')
app.include_router(city.router, tags=['Cities'], prefix='/api/v2/city')
app.include_router(state.router, tags=['States'], prefix='/api/v2/state')
app.include_router(country.router, tags=['Countries'], prefix='/api/v2/country')
app.include_router(product.router, tags=['Products'], prefix='/api/v2/product')
app.include_router(dashboard.router, tags=['Dashboard'], prefix='/api/v2/dashboard')
app.include_router(scan.router, tags=['Scan History'], prefix='/api/v2/scan-history')


@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get('/api/v2')
def root():
    return {'message': 'Hello World'}

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         data = await websocket.receive_text()
#         await websocket.send_text(f"Message text was: {data}")

# Store connected WebSocket clients
websocket_connections = {}
# connected_clients = set()

# @app.websocket("/ws/notifications/{user_id}")
# async def websocket_notifications(websocket: WebSocket, user_id: UUID):
#     await websocket.accept()
#     connected_clients.add((websocket, user_id))

#     try:
#         while True:
#             # Wait for changes in the notifications table and send updates to clients
#             await websocket.receive_text()  # This could be a heartbeat message to keep the connection alive
#     except WebSocketDisconnect:
#         connected_clients.remove((websocket, user_id))
        

# WebSocket endpoint to handle connection
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections['1001'] = websocket

    try:
        while True:
            # Wait for message from client
            data = await websocket.receive_text()
            # if data != "ping":
                # Respond with "pong" message
            await websocket.send_text("pong")
    finally:
        del websocket_connections['1001']
        

# Event listener for handling new notifications
@event.listens_for(models.Notification, "after_insert")
async def receive_after_insert(mapper, connection, target):
    # Fetch connected clients for the user who should receive the notification
    for key, value in websocket_connections.items():
        # if user_id == target.to:
        # Construct notification data to send over WebSocket
        print (key)
        print (value)
        notification_data = {
            "id": str(target.id),
            "message": target.message,
            "created_at": str(target.created_at)
        }
        # Send notification data as JSON to the client
        await value.send_text(json.dumps(notification_data))
            