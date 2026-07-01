from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.order import Order, OrderLog
from ..models.user import User
from ..utils.deps import require_role, get_current_user

router = APIRouter()

class OrderCreate(BaseModel):
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

class StatusUpdate(BaseModel):
    status: str

class ReviewRequest(BaseModel):
    action: str  # approve, reject
    reason: Optional[str] = None

class AssignRequest(BaseModel):
    assigned_to: int

@router.get("/")
async def list_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    region_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单列表（分页 + 筛选）"""
    query = db.query(Order)
    
    # 角色过滤：agent 只能看自己的订单
    if current_user.role == "agent":
        query = query.filter(Order.assigned_to == current_user.id)
    
    # 筛选条件
    if status:
        query = query.filter(Order.status == status)
    if keyword:
        query = query.filter(Order.order_no.contains(keyword) | Order.customer_name.contains(keyword))
    if region_id:
        query = query.filter(Order.region_id == region_id)
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * size
    orders = query.order_by(Order.created_at.desc()).offset(offset).limit(size).all()
    
    order_list = []
    for order in orders:
        order_list.append({
            "id": order.id,
            "order_no": order.order_no,
            "status": order.status,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "customer_address": order.customer_address,
            "product_id": order.product_id,
            "product_name": order.product.name if order.product else None,
            "quantity": order.quantity,
            "unit_price": float(order.unit_price) if order.unit_price else None,
            "total_amount": float(order.total_amount) if order.total_amount else None,
            "region_id": order.region_id,
            "region_name": order.region.name if order.region else None,
            "assigned_to": order.assigned_to,
            "assigned_user": order.assigned_user.display_name if order.assigned_user else None,
            "reviewer_id": order.reviewer_id,
            "reviewer_user": order.reviewer.display_name if order.reviewer else None,
            "reject_reason": order.reject_reason,
            "source_msg_id": order.source_msg_id,
            "remark": order.remark,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None
        })
    
    return {
        "code": 0,
        "data": {
            "items": order_list,
            "total": total,
            "page": page,
            "size": size
        },
        "message": "ok"
    }

@router.get("/{order_id}")
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单详情"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # agent 只能看自己的订单
    if current_user.role == "agent" and order.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此订单"
        )
    
    return {
        "code": 0,
        "data": {
            "id": order.id,
            "order_no": order.order_no,
            "status": order.status,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "customer_address": order.customer_address,
            "product_id": order.product_id,
            "product_name": order.product.name if order.product else None,
            "quantity": order.quantity,
            "unit_price": float(order.unit_price) if order.unit_price else None,
            "total_amount": float(order.total_amount) if order.total_amount else None,
            "region_id": order.region_id,
            "region_name": order.region.name if order.region else None,
            "assigned_to": order.assigned_to,
            "assigned_user": order.assigned_user.display_name if order.assigned_user else None,
            "reviewer_id": order.reviewer_id,
            "reviewer_user": order.reviewer.display_name if order.reviewer else None,
            "reject_reason": order.reject_reason,
            "source_msg_id": order.source_msg_id,
            "remark": order.remark,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None
        },
        "message": "ok"
    }

@router.post("/")
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "reviewer"))
):
    """手动创建订单"""
    # 检查订单号是否已存在
    existing_order = db.query(Order).filter(Order.order_no == order_data.order_no).first()
    if existing_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单号已存在"
        )
    
    # 创建新订单
    new_order = Order(
        order_no=order_data.order_no,
        status="pending_review",
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        customer_address=order_data.customer_address,
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        unit_price=order_data.unit_price,
        total_amount=order_data.total_amount,
        region_id=order_data.region_id,
        remark=order_data.remark
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {
        "code": 0,
        "data": {
            "id": new_order.id,
            "order_no": new_order.order_no,
            "status": new_order.status,
            "customer_name": new_order.customer_name,
            "customer_phone": new_order.customer_phone,
            "customer_address": new_order.customer_address,
            "product_id": new_order.product_id,
            "product_name": new_order.product.name if new_order.product else None,
            "quantity": new_order.quantity,
            "unit_price": float(new_order.unit_price) if new_order.unit_price else None,
            "total_amount": float(new_order.total_amount) if new_order.total_amount else None,
            "region_id": new_order.region_id,
            "region_name": new_order.region.name if new_order.region else None,
            "assigned_to": new_order.assigned_to,
            "assigned_user": new_order.assigned_user.display_name if new_order.assigned_user else None,
            "reviewer_id": new_order.reviewer_id,
            "reviewer_user": new_order.reviewer.display_name if new_order.reviewer else None,
            "reject_reason": new_order.reject_reason,
            "source_msg_id": new_order.source_msg_id,
            "remark": new_order.remark,
            "created_at": new_order.created_at.isoformat() if new_order.created_at else None,
            "updated_at": new_order.updated_at.isoformat() if new_order.updated_at else None
        },
        "message": "ok"
    }

@router.put("/{order_id}")
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "reviewer"))
):
    """更新订单"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 更新字段
    if order_data.customer_name is not None:
        order.customer_name = order_data.customer_name
    if order_data.customer_phone is not None:
        order.customer_phone = order_data.customer_phone
    if order_data.customer_address is not None:
        order.customer_address = order_data.customer_address
    if order_data.product_id is not None:
        order.product_id = order_data.product_id
    if order_data.quantity is not None:
        order.quantity = order_data.quantity
    if order_data.unit_price is not None:
        order.unit_price = order_data.unit_price
    if order_data.total_amount is not None:
        order.total_amount = order_data.total_amount
    if order_data.region_id is not None:
        order.region_id = order_data.region_id
    if order_data.remark is not None:
        order.remark = order_data.remark
    
    db.commit()
    db.refresh(order)

    return {
        "code": 0,
        "data": {
            "id": order.id,
            "order_no": order.order_no,
            "status": order.status,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "customer_address": order.customer_address,
            "product_id": order.product_id,
            "product_name": order.product.name if order.product else None,
            "quantity": order.quantity,
            "unit_price": float(order.unit_price) if order.unit_price else None,
            "total_amount": float(order.total_amount) if order.total_amount else None,
            "region_id": order.region_id,
            "region_name": order.region.name if order.region else None,
            "assigned_to": order.assigned_to,
            "assigned_user": order.assigned_user.display_name if order.assigned_user else None,
            "reviewer_id": order.reviewer_id,
            "reviewer_user": order.reviewer.display_name if order.reviewer else None,
            "reject_reason": order.reject_reason,
            "source_msg_id": order.source_msg_id,
            "remark": order.remark,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None
        },
        "message": "ok"
    }

@router.post("/{order_id}/status")
async def update_order_status(
    order_id: int,
    status_data: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新订单状态"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 验证状态转换合法性
    valid_transitions = {
        "pending_extract": ["pending_review"],
        "pending_review": ["assigned", "rejected"],
        "assigned": ["processing", "cancelled"],
        "processing": ["completed", "cancelled"]
    }
    
    if order.status not in valid_transitions or status_data.status not in valid_transitions[order.status]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"状态转换不合法: {order.status} -> {status_data.status}"
        )
    
    # 记录状态变更日志
    log = OrderLog(
        order_id=order.id,
        operator_id=current_user.id,
        from_status=order.status,
        to_status=status_data.status,
        remark=f"状态变更: {order.status} -> {status_data.status}"
    )
    db.add(log)
    
    # 更新订单状态
    order.status = status_data.status
    db.commit()
    db.refresh(order)
    
    return {
        "code": 0,
        "data": {
            "id": order.id,
            "order_no": order.order_no,
            "status": order.status
        },
        "message": "ok"
    }

@router.post("/{order_id}/review")
async def review_order(
    order_id: int,
    review_data: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("reviewer"))
):
    """审核订单"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 检查订单状态
    if order.status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单状态不是待审核"
        )
    
    if review_data.action == "approve":
        # 审核通过：状态改为 assigned
        new_status = "assigned"
        order.reviewer_id = current_user.id
    elif review_data.action == "reject":
        # 审核驳回：状态改为 rejected
        new_status = "rejected"
        order.reviewer_id = current_user.id
        order.reject_reason = review_data.reason
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的审核操作"
        )
    
    # 记录状态变更日志
    log = OrderLog(
        order_id=order.id,
        operator_id=current_user.id,
        from_status=order.status,
        to_status=new_status,
        remark=f"审核操作: {review_data.action}"
    )
    db.add(log)
    
    # 更新订单状态
    order.status = new_status
    db.commit()
    db.refresh(order)
    
    return {
        "code": 0,
        "data": {
            "id": order.id,
            "order_no": order.order_no,
            "status": order.status,
            "reviewer_id": order.reviewer_id,
            "reject_reason": order.reject_reason
        },
        "message": "ok"
    }

@router.post("/{order_id}/assign")
async def assign_order(
    order_id: int,
    assign_data: AssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "reviewer"))
):
    """分配订单"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 检查订单状态
    if order.status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单状态不是待审核"
        )
    
    # 检查分配用户是否存在且为 agent 角色
    assigned_user = db.query(User).filter(User.id == assign_data.assigned_to).first()
    if not assigned_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分配用户不存在"
        )
    
    if assigned_user.role != "agent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分配用户必须是 agent 角色"
        )
    
    # 记录状态变更日志
    log = OrderLog(
        order_id=order.id,
        operator_id=current_user.id,
        from_status=order.status,
        to_status="assigned",
        remark=f"分配给用户: {assigned_user.username}"
    )
    db.add(log)
    
    # 更新订单
    order.status = "assigned"
    order.assigned_to = assign_data.assigned_to
    order.reviewer_id = current_user.id
    db.commit()
    db.refresh(order)
    
    return {
        "code": 0,
        "data": {
            "id": order.id,
            "order_no": order.order_no,
            "status": order.status,
            "assigned_to": order.assigned_to
        },
        "message": "ok"
    }

@router.get("/{order_id}/logs")
async def get_order_logs(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单操作日志"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    # agent 只能看自己的订单日志
    if current_user.role == "agent" and order.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此订单日志"
        )

    logs = db.query(OrderLog).filter(
        OrderLog.order_id == order_id
    ).order_by(OrderLog.created_at.desc()).all()

    log_list = []
    for log in logs:
        log_list.append({
            "id": log.id,
            "order_id": log.order_id,
            "operator_id": log.operator_id,
            "operator_name": log.operator.username if log.operator else None,
            "from_status": log.from_status,
            "to_status": log.to_status,
            "remark": log.remark,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })

    return {
        "code": 0,
        "data": log_list,
        "message": "ok"
    }