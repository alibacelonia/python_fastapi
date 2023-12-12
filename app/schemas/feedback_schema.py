from datetime import datetime
from typing import List
import uuid
from pydantic import BaseModel, EmailStr, constr
from app.schemas.user_schema import FilteredUserResponse


class FeedbackBaseSchema(BaseModel):
    rate: int = None
    comment: str = None
    user_id: uuid.UUID | None = None
    display_flag: bool = False

    class Config:
        orm_mode = True


class CreateFeedbackSchema(FeedbackBaseSchema):
    pass


class FeedbackResponse(FeedbackBaseSchema):
    id: uuid.UUID
    rate: int
    comment: str
    user: FilteredUserResponse
    display_flag : bool
    created_at: datetime
    updated_at: datetime


class ListFeedbackResponse(BaseModel):
    status: str
    results: int
    feedbacks: List[FeedbackResponse]
