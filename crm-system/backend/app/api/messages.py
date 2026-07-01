from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.raw_message import RawMessage
from ..utils.deps import get_current_user
from ..models.user import User

router = APIRouter()

@router.get("/")
async def list_messages(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    processed: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取原始消息列表（分页 + 筛选）"""
    query = db.query(RawMessage)
    
    # 筛选条件
    if processed is not None:
        query = query.filter(RawMessage.processed == processed)
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * size
    messages = query.order_by(RawMessage.received_at.desc()).offset(offset).limit(size).all()
    
    message_list = []
    for msg in messages:
        message_list.append({
            "id": msg.id,
            "group_name": msg.group_name,
            "group_id": msg.group_id,
            "message_id": msg.message_id,
            "sender_id": msg.sender_id,
            "sender_name": msg.sender_name,
            "text": msg.text,
            "source": msg.source,
            "received_at": msg.received_at.isoformat() if msg.received_at else None,
            "processed": msg.processed
        })
    
    return {
        "code": 0,
        "data": {
            "items": message_list,
            "total": total,
            "page": page,
            "size": size
        },
        "message": "ok"
    }

@router.post("/{message_id}/extract")
async def extract_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """触发消息提取（占位）"""
    # 检查消息是否存在
    message = db.query(RawMessage).filter(RawMessage.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )
    
    # 占位实现：返回成功响应
    return {
        "code": 0,
        "data": None,
        "message": "extraction queued"
    }