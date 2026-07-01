from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from ..database import Base

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(32), unique=True, nullable=False)  # 订单编号
    status = Column(String(20), nullable=False)  # pending_extract, pending_review, rejected, assigned, processing, completed, cancelled
    customer_name = Column(String(128))
    customer_phone = Column(String(32))
    customer_address = Column(String(512))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    unit_price = Column(Numeric(10, 2))
    total_amount = Column(Numeric(12, 2))
    region_id = Column(Integer, ForeignKey("regions.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"))  # 分配给
    reviewer_id = Column(Integer, ForeignKey("users.id"))  # 审核人
    reject_reason = Column(String(512))  # 驳回原因
    source_msg_id = Column(Integer, ForeignKey("raw_messages.id"))  # 来源消息
    remark = Column(Text)  # 备注
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    product = relationship("Product", backref="orders")
    region = relationship("Region", backref="orders")
    assigned_user = relationship("User", foreign_keys=[assigned_to], backref="assigned_orders")
    reviewer = relationship("User", foreign_keys=[reviewer_id], backref="reviewed_orders")
    source_msg = relationship("RawMessage", backref="orders")

class OrderLog(Base):
    __tablename__ = "order_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    from_status = Column(String(32))
    to_status = Column(String(32))
    remark = Column(String(512))
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    order = relationship("Order", backref="logs")
    operator = relationship("User", backref="order_logs")