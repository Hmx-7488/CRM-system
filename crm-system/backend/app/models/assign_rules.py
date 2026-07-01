from sqlalchemy import Column, Integer, String, DateTime, func, JSON
from ..database import Base

class AssignRule(Base):
    __tablename__ = "assign_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    rule_type = Column(String(20), nullable=False)  # region, load_balance, product, custom
    rule_config = Column(JSON)  # 规则配置 JSON
    priority = Column(Integer, default=0)
    status = Column(Integer, default=1)  # 1=启用, 0=禁用
    created_at = Column(DateTime, server_default=func.now())