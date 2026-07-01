from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta
from ..database import get_db
from ..models.order import Order
from ..models.region import Region
from ..utils.deps import get_current_user
from ..models.user import User

router = APIRouter()

@router.get("/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取仪表盘概览统计"""
    # 总订单数
    total_orders = db.query(Order).count()
    
    # 待审核数
    pending_review = db.query(Order).filter(Order.status == "pending_review").count()
    
    # 处理中数
    processing = db.query(Order).filter(Order.status == "processing").count()
    
    # 今日完成数
    today = datetime.now().date()
    completed_today = db.query(Order).filter(
        Order.status == "completed",
        func.date(Order.updated_at) == today
    ).count()
    
    # 区域统计
    region_stats = []
    regions = db.query(Region).filter(Region.status == 1).all()
    for region in regions:
        count = db.query(Order).filter(Order.region_id == region.id).count()
        region_stats.append({
            "region_name": region.name,
            "count": count
        })
    
    return {
        "code": 0,
        "data": {
            "total_orders": total_orders,
            "pending_review": pending_review,
            "processing": processing,
            "completed_today": completed_today,
            "region_stats": region_stats
        },
        "message": "ok"
    }

@router.get("/orders")
async def get_order_statistics(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取近 N 天每日各状态订单数"""
    # 计算日期范围
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # 查询每日各状态订单数
    daily_stats = []
    current_date = start_date
    
    while current_date <= end_date:
        # 查询当天各状态订单数
        stats = db.query(
            func.count(case((Order.status == "pending_review", 1))).label("pending_review"),
            func.count(case((Order.status == "assigned", 1))).label("assigned"),
            func.count(case((Order.status == "processing", 1))).label("processing"),
            func.count(case((Order.status == "completed", 1))).label("completed"),
            func.count(case((Order.status == "cancelled", 1))).label("cancelled")
        ).filter(
            func.date(Order.created_at) == current_date
        ).first()
        
        daily_stats.append({
            "date": current_date.isoformat(),
            "pending_review": stats.pending_review if stats else 0,
            "assigned": stats.assigned if stats else 0,
            "processing": stats.processing if stats else 0,
            "completed": stats.completed if stats else 0,
            "cancelled": stats.cancelled if stats else 0
        })
        
        current_date += timedelta(days=1)
    
    return {
        "code": 0,
        "data": daily_stats,
        "message": "ok"
    }