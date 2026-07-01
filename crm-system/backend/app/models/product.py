from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from ..database import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    spec = Column(String(128))  # 规格
    category = Column(String(64))  # 品类
    unit_price = Column(Numeric(10, 2))  # 单价
    unit = Column(String(16))  # 单位 (箱/件/个)
    source = Column(String(20))  # manual, auto
    source_msg_id = Column(Integer, ForeignKey("raw_messages.id"))  # 来源消息
    status = Column(String(20), default="active")  # active, inactive
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    source_msg = relationship("RawMessage", backref="products")