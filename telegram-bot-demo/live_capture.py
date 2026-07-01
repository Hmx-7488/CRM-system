"""
Real-time Telegram group message capture using the Bot API.

Requires the bot to be added to the target group with privacy mode DISABLED.
The bot will capture every message it sees and write them to a JSON lines file.

Note: Bot API can only see messages sent AFTER the bot joined the group.
      Use dump_messages.py with Telethon for historical messages.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import MessageOriginType

# --- Config ----------------------------------------------------------------

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN or TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("ERROR: Set TELEGRAM_BOT_TOKEN environment variable.")
    print("  Copy .env.example to .env and fill in your bot token from @BotFather.")
    sys.exit(1)

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "./output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Build output filename with timestamp
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_PATH = OUTPUT_DIR / f"live_capture_{ts}.jsonl"

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("live_capture")


# --- Message serialisation ------------------------------------------------

def serialise_message(update: Update) -> dict | None:
    """Extract key fields from an incoming Telegram message update."""
    msg = update.effective_message
    if msg is None:
        return None

    user = msg.from_user
    chat = msg.chat

    record = {
        "message_id": msg.message_id,
        "date": msg.date.astimezone(timezone.utc).isoformat() if msg.date else None,
        "chat_id": chat.id if chat else None,
        "chat_title": getattr(chat, "title", None) if chat else None,
        "chat_type": chat.type if chat else None,
        "from_user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_bot": user.is_bot,
        } if user else None,
        "text": msg.text or msg.caption or None,
        "has_media": bool(msg.photo or msg.video or msg.document or msg.audio or msg.voice or msg.sticker),
        "media_types": _collect_media_types(msg),
        "is_reply": msg.reply_to_message is not None,
        "reply_to_msg_id": msg.reply_to_message.message_id if msg.reply_to_message else None,
        "forward_origin": _serialise_forward(msg),
        "entities": _serialise_entities(msg),
        "pinned_message": serialize_pinned(msg) if msg.pinned_message else None,
    }
    return record


def _collect_media_types(msg) -> list:
    types = []
    if msg.photo:       types.append("photo")
    if msg.video:       types.append("video")
    if msg.document:    types.append("document")
    if msg.audio:       types.append("audio")
    if msg.voice:       types.append("voice")
    if msg.sticker:     types.append("sticker")
    if msg.animation:   types.append("animation")
    if msg.video_note:  types.append("video_note")
    if msg.contact:     types.append("contact")
    if msg.location:    types.append("location")
    if msg.venue:       types.append("venue")
    if msg.poll:        types.append("poll")
    if msg.dice:        types.append("dice")
    if msg.game:        types.append("game")
    return types


def _serialise_forward(msg) -> dict | None:
    """Extract forward origin info."""
    fo = getattr(msg, "forward_origin", None)
    if fo is None:
        return None

    base = {"type": fo.type}
    if fo.type == MessageOriginType.USER:
        base["sender_user"] = {
            "id": fo.sender_user.id,
            "username": fo.sender_user.username,
            "first_name": fo.sender_user.first_name,
        }
        base["date"] = fo.date.isoformat() if fo.date else None
    elif fo.type == MessageOriginType.CHANNEL:
        base["chat_id"] = fo.chat.id
        base["chat_title"] = fo.chat.title
        base["message_id"] = fo.message_id
        base["date"] = fo.date.isoformat() if fo.date else None
    elif fo.type == MessageOriginType.HIDDEN_USER:
        base["sender_user_name"] = fo.sender_user_name
        base["date"] = fo.date.isoformat() if fo.date else None
    return base


def _serialise_entities(msg) -> list | None:
    if not msg.entities:
        return None
    result = []
    for e in msg.entities:
        result.append({
            "type": e.type,
            "offset": e.offset,
            "length": e.length,
            "url": getattr(e, "url", None),
            "language": getattr(e, "language", None),
        })
    return result


def serialize_pinned(msg) -> dict | None:
    """Minimal serialisation of a pinned message."""
    pm = msg.pinned_message
    if pm is None:
        return None
    return {
        "message_id": pm.message_id,
        "date": pm.date.astimezone(timezone.utc).isoformat() if pm.date else None,
        "text": pm.text or pm.caption or None,
    }


# --- Handler --------------------------------------------------------------

async def capture_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Capture every incoming message and write to file."""
    record = serialise_message(update)
    if record is None:
        return

    try:
        with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        chat_title = record.get("chat_title") or f"chat_{record['chat_id']}"
        sender = record["from_user"]["first_name"] if record["from_user"] else "unknown"
        text_preview = (record["text"] or "[media]")[:60].replace("\n", " ")
        logger.info("[%s] %s: %s", chat_title, sender, text_preview)

    except Exception:
        logger.exception("Failed to write message")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Update caused error: %s", context.error)


# --- Main -----------------------------------------------------------------

def main():
    logger.info("Starting live capture bot...")
    logger.info("Output file: %s", OUTPUT_PATH)

    app = Application.builder().token(TOKEN).build()

    # Capture ALL message types - text, media, polls, etc.
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        capture_message,
    ))
    app.add_error_handler(error_handler)

    logger.info("Bot is running. Press Ctrl+C to stop.")
    logger.info("Make sure the bot is an admin in the target group with privacy mode OFF.")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
