from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    spec: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    unit: Optional[str] = None
    source: Optional[str] = "manual"
    source_msg_id: Optional[int] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    spec: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    unit: Optional[str] = None
    status: Optional[str] = None

class ProductResponse(ProductBase):
    id: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True