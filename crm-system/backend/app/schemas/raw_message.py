from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RawMessageBase(BaseModel):
    group_name: Optional[str] = None
    group_id: Optional[int] = None
    message_id: Optional[int] = None
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    text: Optional[str] = None
    source: Optional[str] = None
    received_at: Optional[datetime] = None

class RawMessageCreate(RawMessageBase):
    pass

class RawMessageResponse(RawMessageBase):
    id: int
    processed: int
    
    class Config:
        from_attributes = True