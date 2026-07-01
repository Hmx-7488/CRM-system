from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RegionBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class RegionCreate(RegionBase):
    pass

class RegionUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None

class RegionResponse(RegionBase):
    id: int
    status: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True