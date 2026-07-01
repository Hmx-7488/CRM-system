from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OrderBase(BaseModel):
    order_no: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None
    region_id: Optional[int] = None
    remark: Optional[str] = None

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None
    region_id: Optional[int] = None
    remark: Optional[str] = None

class OrderResponse(OrderBase):
    id: int
    status: str
    assigned_to: Optional[int] = None
    reviewer_id: Optional[int] = None
    reject_reason: Optional[str] = None
    source_msg_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: str

class OrderReview(BaseModel):
    action: str  # approve, reject
    reason: Optional[str] = None

class OrderAssign(BaseModel):
    assigned_to: int

class OrderLogResponse(BaseModel):
    id: int
    order_id: int
    operator_id: int
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True