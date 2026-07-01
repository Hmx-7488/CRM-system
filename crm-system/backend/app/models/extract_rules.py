from sqlalchemy import Column, Integer, String, DateTime, func, JSON
from ..database import Base

class ExtractRule(Base):
    __tablename__ = "extract_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    rule_type = Column(String(20), nullable=False)  # keyword, regex, sender, group
    rule_config = Column(JSON)  # 规则配置 JSON
    priority = Column(Integer, default=0)
    status = Column(Integer, default=1)  # 1=启用, 0=禁用
    created_at = Column(DateTime, server_default=func.now())