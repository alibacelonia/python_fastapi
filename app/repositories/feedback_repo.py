import os
from pathlib import Path
import shutil
from typing import List
import uuid

from pydantic import EmailStr
from sqlalchemy import func, select, update

from app import utils
from app.email import Email
from app.schemas.user_schema import CreateUserSchema, FilteredUserResponse
from .. import models
from ..schemas.feedback_schema import FeedbackBaseSchema, FeedbackResponse, ListFeedbackResponse, CreateFeedbackSchema, UpdateFeedbackSchema
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, UploadFile, status, APIRouter, Response
from ..database import get_session
from app.oauth2 import require_user
from ..repositories import user_repo

router = APIRouter()


USERDATA_DIR = os.path.join("app", "userdata")

# get feedbacks without authentication
async def get_feedbacks(db: Session, limit: int, page: int, search: str):
    skip = (page - 1) * limit
    
    query = await db.execute(
            select(models.Feedback, models.User).join(models.User).where(models.Feedback.user_id == models.User.id)
            .group_by(models.Feedback.id, models.User.id)
            .limit(limit)
            .offset(skip)
        )
    
    feedbacks_with_users = query.fetchall()
    
    feedbacks_response: List[FeedbackResponse] = []
    for feedback, user in feedbacks_with_users:
        feedback.user = user
        feedbacks_response.append(feedback)
    
    return {'status': 'success', 'results': len(feedbacks_response), 'feedbacks': feedbacks_response}

# get feedbacks with authentication
async def get_my_all_feedbacks(db: Session, user_id: str):
    query = await db.execute(
            select(models.Feedback)
            .group_by(models.Feedback.id)
            .where(models.Feedback.owner_id == user_id)
    )
    feedbacks = query.scalars().all()
    return {'status': 'success', 'results': len(feedbacks), 'feedbacks': feedbacks}

# create feedback without authentication
async def create_feedback(feedback: CreateFeedbackSchema, db: Session):
    new_feedback = models.Feedback(**feedback.dict())
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return new_feedback

# update feedback without authentication
async def update_feedback(id: str, feedback: UpdateFeedbackSchema, db: Session):
    
    feedback_query = await db.execute(
            select(models.Feedback).where(models.Feedback.unique_id == id)
        )
    selected_feedback = feedback_query.scalar_one_or_none()
    if not selected_feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Feedback not found')
        
    if selected_feedback is not None:
            for key, value in feedback.dict(exclude_unset=True).items():
                setattr(selected_feedback, key, value)
            await db.commit()
    return selected_feedback

# update feedback with authentication
async def update_my_feedback(id: str, feedback: UpdateFeedbackSchema, db: Session, user_id: str):
    
    feedback_query = await db.execute(
            select(models.Feedback).where(models.Feedback.unique_id == id)
        )
    updated_feedback:FeedbackBaseSchema = feedback_query.scalar_one_or_none()

    if not updated_feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Feedback not found')
    if feedback.owner_id != uuid.UUID(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not allowed to perform this action')
    if updated_feedback is not None:
            for key, value in feedback.dict(exclude_unset=True).items():
                setattr(updated_feedback, key, value)
            await db.commit()
    return updated_feedback
