from collections import defaultdict
import uuid

from sqlalchemy import select

from ..schemas.feedback_schema import FeedbackResponse, ListFeedbackResponse, CreateFeedbackSchema
from .. import models
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, APIRouter, Response
from ..database import get_session
from app.oauth2 import require_user
from ..repositories import dashboard_repo
router = APIRouter()


# @router.get('/')
@router.get('/dashboard-data-counts')
async def get_feedbacks(db: Session = Depends(get_session), user_id: str = Depends(require_user)):
    
    users = await dashboard_repo.get_users(db)
    pets = await dashboard_repo.get_pets(db)
    feedbacks = await dashboard_repo.get_feedbacks(db)
    
    user_counts = defaultdict(int)
    pet_counts = defaultdict(int)
    order_counts = defaultdict(int)
    feedback_counts = defaultdict(int)

    for user in users:
        user_counts["verified" if user.verified else "not_verified"] += 1
        user_counts["total"] += 1
        
        
    for pet in pets:
        pet_counts["taken" if pet.owner_id is not None else "available"] += 1
        pet_counts["total"] += 1
        
    for feedback in feedbacks:
        feedback_counts["total"] += 1
        
    order_counts["total"] = 0
    
    return {
        'user': user_counts, 
        'qrcode': pet_counts,
        'feedback': feedback_counts, 
        'order': order_counts
    }

    