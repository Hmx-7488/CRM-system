import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.assign_rules import AssignRule
from ..models.user import User
from ..models.order import Order

logger = logging.getLogger(__name__)


def _seed_assign_rules_if_empty(db: Session):
    """首次运行且 assign_rules 为空时自动创建种子规则"""
    count = db.query(AssignRule).count()
    if count > 0:
        return

    rule = AssignRule(
        name="华东默认分配",
        rule_type="region",
        rule_config={"region_id": 1, "agent_ids": []},
        priority=10,
        status=1
    )
    db.add(rule)
    db.commit()
    logger.info("已创建预置分配规则: 华东默认分配")


def _get_least_busy_agent(db: Session, region_id: int) -> int | None:
    """查询指定区域中当前订单数最少的 agent"""
    # 查询该区域所有启用 agent
    agents = (
        db.query(User)
        .filter(User.role == "agent", User.region_id == region_id, User.status == 1)
        .all()
    )
    if not agents:
        return None

    # 统计每个 agent 当前 assigned + processing 的订单数
    agent_ids = [a.id for a in agents]
    busy_counts = (
        db.query(Order.assigned_to, func.count(Order.id))
        .filter(
            Order.assigned_to.in_(agent_ids),
            Order.status.in_(["assigned", "processing"])
        )
        .group_by(Order.assigned_to)
        .all()
    )
    count_map = {uid: cnt for uid, cnt in busy_counts}

    # 选择订单数最少的 agent
    least_busy = min(agents, key=lambda a: count_map.get(a.id, 0))
    return least_busy.id


def auto_assign(db: Session, order: Order) -> int | None:
    """
    按优先级匹配分配规则，返回应分配的 user_id。
    无匹配规则时返回 None。
    """
    _seed_assign_rules_if_empty(db)

    # 如果订单没有区域，无法分配
    if not order.region_id:
        return None

    # 加载所有启用的规则，按 priority DESC
    rules = (
        db.query(AssignRule)
        .filter(AssignRule.status == 1)
        .order_by(AssignRule.priority.desc())
        .all()
    )

    for rule in rules:
        config = rule.rule_config or {}

        if rule.rule_type == "region":
            if config.get("region_id") != order.region_id:
                continue
            agent_ids = config.get("agent_ids", [])
            if agent_ids:
                # 分配给列表中第一个启用的 agent
                for agent_id in agent_ids:
                    user = db.query(User).filter(
                        User.id == agent_id,
                        User.role == "agent",
                        User.status == 1
                    ).first()
                    if user:
                        return user.id
                # 列表中无可用 agent，继续下一条规则
                continue
            else:
                # 未指定 agent_ids，负载均衡
                return _get_least_busy_agent(db, order.region_id)

        elif rule.rule_type == "load_balance":
            target_region = config.get("region_id")
            if target_region is not None and target_region != order.region_id:
                continue
            return _get_least_busy_agent(db, order.region_id)

        # product / custom 暂不处理

    return None
