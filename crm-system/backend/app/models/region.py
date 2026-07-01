from sqlalchemy import Column, Integer, String, DateTime, func
from ..database import Base

class Region(Base):
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)
    code = Column(String(16), unique=True, nullable=False)
    description = Column(String(256))
    status = Column(Integer, default=1)  # 1=启用, 0=禁用
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())