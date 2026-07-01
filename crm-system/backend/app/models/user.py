from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    display_name = Column(String(64))
    role = Column(String(20), nullable=False)  # admin, reviewer, agent
    region_id = Column(Integer, ForeignKey("regions.id"))
    status = Column(Integer, default=1)  # 1=启用, 0=禁用
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    region = relationship("Region", backref="users")