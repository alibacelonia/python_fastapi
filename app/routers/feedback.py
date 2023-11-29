import uuid

from sqlalchemy import select

from ..schemas.feedback_schema import FeedbackResponse, ListFeedbackResponse, CreateFeedbackSchema, UpdateFeedbackSchema
from .. import models
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, APIRouter, Response
from ..database import get_session
from app.oauth2 import require_user
from ..repositories import feedback_repo
router = APIRouter()


# @router.get('/')
@router.get('/', response_model=ListFeedbackResponse)
async def get_feedbacks(db: Session = Depends(get_session), limit: int = 10, page: int = 1, search: str = '', user_id: str = Depends(require_user)):
    response = await feedback_repo.get_feedbacks(db, limit, page, search)
    return response


# @router.post('/', status_code=status.HTTP_201_CREATED)
@router.post('/', status_code=status.HTTP_201_CREATED, response_model=FeedbackResponse)
async def create_feedback(feedback: CreateFeedbackSchema, db: Session = Depends(get_session), owner_id: str = Depends(require_user)):
    try:
        user_query = await db.execute(
            select(models.User).where(models.User.id == owner_id)
        )
        
        user: models.User = user_query.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not logged authenticated')
            
            
        # feedback_query = await db.execute(
        #     select(models.Feedback).where(models.Feedback.user_id == owner_id)
        # )
        
        # feedback_db: models.Feedback = feedback_query.scalar_one_or_none()
        # if feedback_db is not None:
        #     raise HTTPException(status_code=status.HTTP_409_CONFLICT,
        #                     detail='Already submitted a feedback')
            
        
        feedback.user_id = uuid.UUID(owner_id)
        new_feedback = models.Feedback(**feedback.dict())
        
        db.add(new_feedback)
        await db.commit()
        await db.refresh(new_feedback)
        new_feedback.user = user
        return new_feedback
        
    except Exception as e:
        raise e

@router.get('/check')
async def get_feedbacks(db: Session = Depends(get_session), user_id: str = Depends(require_user)):

    query = await db.execute(
            select(models.Feedback).where(models.Feedback.user_id == user_id)
        )
    
    feedback = query.first()
        
    return {"hasFeedback": False if not feedback else True}
    