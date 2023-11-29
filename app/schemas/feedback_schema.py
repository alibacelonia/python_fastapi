from datetime import datetime
from typing import List
import uuid
from pydantic import BaseModel, EmailStr, constr
from app.schemas.user_schema import FilteredUserResponse


class FeedbackBaseSchema(BaseModel):
    rate: int = None
    comment: str = None
    user_id: uuid.UUID | None = None

    class Config:
        orm_mode = True


class CreateFeedbackSchema(FeedbackBaseSchema):
    pass


class FeedbackResponse(FeedbackBaseSchema):
    id: uuid.UUID
    rate: int
    comment: str
    user: FilteredUserResponse
    created_at: datetime
    updated_at: datetime


class UpdateFeedbackSchema(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    image: str | None = None
    user_id: uuid.UUID | None = None

    class Config:
        orm_mode = True


class ListFeedbackResponse(BaseModel):
    status: str
    results: int
    feedbacks: List[FeedbackResponse]
