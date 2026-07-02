from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..database import get_db
from ..models.raw_message import RawMessage
from ..models.order import Order
from ..utils.deps import get_current_user
from ..models.user import User
from ..services.import_service import import_messages
from ..services.extract_service import run_extraction
from ..services.order_service import create_order_log

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

@router.post("/batch-extract")
async def batch_extract(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量提取所有未处理消息"""
    unprocessed = db.query(RawMessage).filter(
        RawMessage.processed == 0,
        RawMessage.text.isnot(None),
        RawMessage.text != ""
    ).all()

    results = {"total": len(unprocessed), "matched": 0, "created_orders": 0, "skipped": 0}

    for msg in unprocessed:
        result = run_extraction(db, msg)
        if result["matched"]:
            fields = result["extracted_fields"]
            order = Order(
                order_no=f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{msg.id}",
                status="pending_review",
                source_msg_id=msg.id,
                remark="批量自动提取"
            )
            for field, value in fields.items():
                if hasattr(order, field):
                    setattr(order, field, value)
            db.add(order)
            db.flush()
            create_order_log(db, order.id, current_user.id, None, "pending_review", "批量自动提取")
            msg.processed = 1
            results["matched"] += 1
            results["created_orders"] += 1
        else:
            results["skipped"] += 1

    db.commit()

    return {
        "code": 0,
        "data": results,
        "message": f"处理 {results['total']} 条，生成 {results['created_orders']} 个订单"
    }


@router.post("/{message_id}/extract")
async def extract_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """触发单条消息提取"""
    msg = db.query(RawMessage).filter(RawMessage.id == message_id).first()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )

    result = run_extraction(db, msg)

    if not result["matched"]:
        return {
            "code": 0,
            "data": {"matched": False, "reason": "no rule matched"},
            "message": "未匹配到任何规则"
        }

    fields = result["extracted_fields"]
    order = Order(
        order_no=f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{msg.id}",
        status="pending_review",
        customer_name=fields.get("customer_name"),
        customer_phone=fields.get("customer_phone"),
        customer_address=fields.get("customer_address"),
        quantity=fields.get("quantity"),
        unit_price=fields.get("unit_price"),
        total_amount=fields.get("total_amount"),
        region_id=fields.get("region_id"),
        source_msg_id=msg.id,
        remark=f"自动提取自消息 #{msg.id}"
    )
    db.add(order)
    msg.processed = 1
    db.commit()
    db.refresh(order)

    create_order_log(db, order.id, current_user.id, None, "pending_review", "自动提取")

    return {
        "code": 0,
        "data": {
            "order_id": order.id,
            "order_no": order.order_no,
            "matched_rules": result["triggered_rules"],
            "extracted_fields": fields
        },
        "message": "提取成功"
    }

class ImportRequest(BaseModel):
    content: str        # JSONL 文件内容
    source: str = "history"  # 'history' 或 'live'

@router.post("/import")
async def import_messages_api(
    req: ImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导入 JSONL 消息"""
    result = import_messages(db, req.content, req.source)
    return {
        "code": 0,
        "data": result,
        "message": f"导入 {result['imported']} 条，跳过 {result['skipped']} 条"
    }