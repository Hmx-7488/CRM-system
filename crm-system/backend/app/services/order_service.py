from sqlalchemy.orm import Session
from ..models.order import Order, OrderLog
from ..models.user import User

def create_order_log(db: Session, order_id: int, operator_id: int, from_status: str, to_status: str, remark: str = None):
    """创建订单日志"""
    log = OrderLog(
        order_id=order_id,
        operator_id=operator_id,
        from_status=from_status,
        to_status=to_status,
        remark=remark
    )
    db.add(log)
    return log

def get_order_logs(db: Session, order_id: int):
    """获取订单日志"""
    return db.query(OrderLog).filter(OrderLog.order_id == order_id).order_by(OrderLog.created_at.desc()).all()