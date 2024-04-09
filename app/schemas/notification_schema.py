from datetime import datetime
from typing import List
import uuid
from pydantic import BaseModel, EmailStr, constr
from app.schemas.user_schema import FilteredUserResponse


class NotificationBaseSchema(BaseModel):
    to: str
    message: str

    class Config:
        orm_mode = True


class CreateNotificationSchema(NotificationBaseSchema):
    created_at : datetime = None
    is_read: bool = False


class NotificationResponse(NotificationBaseSchema):
    id: uuid.UUID
    to: str
    message: str
    created_at : datetime
    is_read: bool
    created_at: datetime

