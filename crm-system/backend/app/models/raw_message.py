from sqlalchemy import Column, Integer, String, DateTime, func, Text, JSON, BigInteger
from ..database import Base

class RawMessage(Base):
    __tablename__ = "raw_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_name = Column(String(128))
    group_id = Column(BigInteger)
    message_id = Column(Integer)
    sender_id = Column(BigInteger)
    sender_name = Column(String(128))
    text = Column(Text)
    raw_json = Column(JSON)  # 原始消息完整 JSON
    source = Column(String(20))  # history, live
    received_at = Column(DateTime)
    processed = Column(Integer, default=0)  # 0=未处理, 1=已处理