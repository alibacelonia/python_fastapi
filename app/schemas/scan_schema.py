from datetime import datetime
from typing import List
import uuid
from pydantic import BaseModel, EmailStr, constr
from app.schemas.user_schema import FilteredUserResponse


class ScanSchema(BaseModel):
    qr_code_id: str
    scanned_by: str = "Anonymous"
    scan_time: datetime = None
    location: str = None
    scan_result: str = None
    device_info: str = None
    ip_address: str = None
    user_agent: str = None

    class Config:
        orm_mode = True
    
