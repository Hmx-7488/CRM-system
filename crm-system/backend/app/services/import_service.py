import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.raw_message import RawMessage

logger = logging.getLogger(__name__)


def _parse_sender_name(data: dict, fmt: str) -> str:
    """从格式 A/B 中提取发送者名称"""
    if fmt == "A":
        sender = data.get("sender") or {}
    else:
        sender = data.get("from_user") or {}

    first = (sender.get("first_name") or "").strip()
    last = (sender.get("last_name") or "").strip()
    name = f"{first} {last}".strip()
    return name or None


def _detect_and_map(line_data: dict, source: str) -> dict | None:
    """
    自动检测 JSONL 行的格式 (A / B)，并映射为 raw_messages 字段。
    返回 None 表示无法识别，应跳过。
    """
    if "from_user" in line_data:
        fmt = "B"
    elif "sender" in line_data:
        fmt = "A"
    else:
        return None

    group_id = line_data.get("chat_id")
    message_id = line_data.get("message_id") if fmt == "B" else line_data.get("id")

    if group_id is None or message_id is None:
        return None

    # group_name
    group_name = line_data.get("chat_title")
    if not group_name:
        group_name = f"chat_{group_id}"

    # sender_id
    if fmt == "A":
        sender = line_data.get("sender") or {}
    else:
        sender = line_data.get("from_user") or {}
    sender_id = sender.get("id")

    # sender_name
    sender_name = _parse_sender_name(line_data, fmt)

    # text
    text = line_data.get("text") or ""

    # received_at
    date_str = line_data.get("date")
    received_at = None
    if date_str:
        try:
            received_at = datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            pass

    return {
        "group_name": group_name,
        "group_id": group_id,
        "message_id": message_id,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "text": text,
        "raw_json": line_data,
        "source": source,
        "received_at": received_at,
        "processed": 0,
    }


def import_messages(db: Session, jsonl_content: str, source: str = "history") -> dict:
    """
    解析 JSONL 内容并导入 raw_messages 表。

    参数:
        db: SQLAlchemy 数据库 session
        jsonl_content: JSONL 文件的完整文本内容
        source: 'history' 或 'live'

    返回:
        {"imported": N, "skipped": M, "errors": K, "total": N+M+K}
    """
    imported = 0
    skipped = 0
    errors = 0

    lines = jsonl_content.strip().splitlines()

    for line_no, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue

        # 1. JSON 解析
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            logger.warning(f"Line {line_no}: JSON 解析失败")
            errors += 1
            continue

        # 2. 格式检测 & 字段映射
        mapped = _detect_and_map(data, source)
        if mapped is None:
            logger.warning(f"Line {line_no}: 无法识别的消息格式，跳过")
            errors += 1
            continue

        # 3. 去重：(group_id, message_id)
        exists = (
            db.query(RawMessage.id)
            .filter(
                RawMessage.group_id == mapped["group_id"],
                RawMessage.message_id == mapped["message_id"],
            )
            .first()
        )
        if exists:
            skipped += 1
            continue

        # 4. 写入
        db.add(RawMessage(**mapped))
        imported += 1

        # 5. 每 100 条 flush
        if imported % 100 == 0:
            db.flush()

    # 6. 最终 commit
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"数据库提交失败: {e}")
        return {"imported": 0, "skipped": 0, "errors": len(lines), "total": len(lines)}

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "total": imported + skipped + errors,
    }
