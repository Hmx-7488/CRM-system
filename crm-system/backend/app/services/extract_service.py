import re
import logging
from sqlalchemy.orm import Session
from ..models.raw_message import RawMessage
from ..models.extract_rules import ExtractRule

logger = logging.getLogger(__name__)


def _seed_rules_if_empty(db: Session):
    """首次运行时如果 extract_rules 表为空，自动创建两条示例规则"""
    count = db.query(ExtractRule).count()
    if count > 0:
        return

    rules = [
        ExtractRule(
            name="订单触发词",
            rule_type="keyword",
            rule_config={"keywords": ["下单", "订购", "来货", "要货"]},
            priority=10,
            status=1
        ),
        ExtractRule(
            name="金额提取",
            rule_type="regex",
            rule_config={
                "pattern": r"[¥￥](\d+(?:\.\d{1,2})?)",
                "field_mapping": {"total_amount": 1}
            },
            priority=5,
            status=1
        )
    ]
    db.add_all(rules)
    db.commit()
    logger.info("已创建 %d 条预置提取规则", len(rules))


def _match_keyword(text: str, config: dict) -> bool:
    keywords = config.get("keywords", [])
    return any(kw in text for kw in keywords)


def _match_regex(text: str, config: dict):
    """返回 (matched: bool, extracted_fields: dict)"""
    pattern = config.get("pattern", "")
    if not pattern:
        return False, {}
    m = re.search(pattern, text)
    if not m:
        return False, {}
    field_mapping = config.get("field_mapping", {})
    extracted = {}
    for field_name, group_idx in field_mapping.items():
        try:
            extracted[field_name] = m.group(group_idx)
        except (IndexError, AttributeError):
            pass
    return True, extracted


def run_extraction(db: Session, message: RawMessage) -> dict:
    """
    对一条消息执行所有启用的提取规则。

    返回:
      {
        "matched": bool,
        "triggered_rules": [...],
        "extracted_fields": {...},
      }
    """
    # 确保有种子规则
    _seed_rules_if_empty(db)
    db.refresh(message)  # 刷新以获取最新数据

    # 加载所有启用的规则，按 priority DESC
    rules = (
        db.query(ExtractRule)
        .filter(ExtractRule.status == 1)
        .order_by(ExtractRule.priority.desc())
        .all()
    )

    text = message.text or ""
    triggered_rules = []
    extracted_fields = {}

    for rule in rules:
        config = rule.rule_config or {}
        matched = False

        if rule.rule_type == "keyword":
            matched = _match_keyword(text, config)
        elif rule.rule_type == "regex":
            matched, fields = _match_regex(text, config)
            if matched:
                extracted_fields.update(fields)
        elif rule.rule_type == "sender":
            sender_ids = config.get("sender_ids", [])
            matched = message.sender_id in sender_ids
        elif rule.rule_type == "group":
            group_ids = config.get("group_ids", [])
            matched = message.group_id in group_ids

        if matched:
            triggered_rules.append(rule.name)

    return {
        "matched": len(triggered_rules) > 0,
        "triggered_rules": triggered_rules,
        "extracted_fields": extracted_fields,
    }
