import json
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class UserEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            # If the object is a UUID, convert it to a string
            return str(obj)
        elif isinstance(obj, datetime):
            # If the object is a datetime, convert it to a string
            return obj.isoformat()
        elif isinstance(obj.__class__, DeclarativeMeta):
            # If the object is an SQLAlchemy model, convert it to a dictionary
            return {col.name: getattr(obj, col.name) for col in obj.__table__.columns}
        return super().default(obj)