"""
Export ALL messages from a Telegram group chat using Telethon (MTProto API).

Step-by-step login:
  python dump_messages.py --phone +8613800138000
  # sends code, then prompts for code + 2FA, all in one run
"""

import argparse
import asyncio
import getpass
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from telethon import TelegramClient, errors
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
    MessageMediaWebPage,
    MessageMediaPoll,
    MessageMediaGeo,
    MessageMediaVenue,
    MessageMediaContact,
    MessageMediaDice,
    MessageMediaGame,
    MessageMediaGiveaway,
    MessageMediaStory,
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("dump")


def env_or_raise(key: str) -> str:
    val = os.environ.get(key, "").strip()
    if not val or val.startswith("YOUR_"):
        raise SystemExit(f"Missing env: {key}")
    return val


def serialise_sender(sender) -> dict:
    if sender is None:
        return {"id": None, "username": None, "first_name": None, "last_name": None}
    return {
        "id": sender.id,
        "username": getattr(sender, "username", None),
        "first_name": getattr(sender, "first_name", None),
        "last_name": getattr(sender, "last_name", None),
        "display_name": getattr(sender, "first_name", None) or getattr(sender, "title", None),
    }


def serialise_media(msg) -> dict | None:
    media = msg.media
    if media is None:
        return None
    base = {}
    if isinstance(media, MessageMediaPhoto):
        base["type"] = "photo"
        if hasattr(media, "photo") and media.photo:
            base["id"] = media.photo.id
    elif isinstance(media, MessageMediaDocument):
        base["type"] = "document"
        if hasattr(media, "document") and media.document:
            doc = media.document
            base["id"] = doc.id
            base["size"] = doc.size
            base["mime_type"] = doc.mime_type
            for attr in doc.attributes:
                if type(attr).__name__ == "DocumentAttributeFilename":
                    base["filename"] = attr.file_name
    elif isinstance(media, MessageMediaWebPage):
        base["type"] = "webpage"
        base["url"] = getattr(media.webpage, "url", None) if media.webpage else None
    elif isinstance(media, MessageMediaPoll):
        base["type"] = "poll"
    elif isinstance(media, MessageMediaGeo):
        base["type"] = "geo"
    elif isinstance(media, MessageMediaVenue):
        base["type"] = "venue"
    elif isinstance(media, MessageMediaContact):
        base["type"] = "contact"
    elif isinstance(media, MessageMediaDice):
        base["type"] = "dice"
    elif isinstance(media, MessageMediaGame):
        base["type"] = "game"
    elif isinstance(media, MessageMediaGiveaway):
        base["type"] = "giveaway"
    elif isinstance(media, MessageMediaStory):
        base["type"] = "story"
    else:
        base["type"] = media.__class__.__name__
    return base



def _serialise_peer(peer) -> dict | None:
    if peer is None:
        return None
    if hasattr(peer, "user_id"):
        return {"type": "user", "user_id": peer.user_id}
    if hasattr(peer, "channel_id"):
        return {"type": "channel", "channel_id": peer.channel_id}
    if hasattr(peer, "chat_id"):
        return {"type": "chat", "chat_id": peer.chat_id}
    return {"type": peer.__class__.__name__}


def serialise_message(msg) -> dict:
    return {
        "id": msg.id,
        "date": msg.date.astimezone(timezone.utc).isoformat(),
        "text": msg.text,
        "raw_text": getattr(msg, "raw_text", None),
        "sender": serialise_sender(msg.sender),
        "sender_id": _serialise_peer(getattr(msg, "from_id", None)),
        "chat_id": msg.chat_id,
        "is_reply": msg.is_reply,
        "reply_to_msg_id": msg.reply_to_msg_id,
        "forwarded": msg.forward is not None,
        "forward_from": msg.forward.original_friendly_name if msg.forward else None,
        "pinned": getattr(msg, "pinned", False),
        "edited": msg.edit_date is not None,
        "edit_date": msg.edit_date.astimezone(timezone.utc).isoformat() if msg.edit_date else None,
        "media": serialise_media(msg),
        "has_media": msg.media is not None,
        "grouped_id": getattr(msg, "grouped_id", None),
        "reactions": _serialise_reactions(msg),
        "views": getattr(msg, "views", None),
        "forwards": getattr(msg, "forwards", None),
    }


def _serialise_reactions(msg) -> list | None:
    if not hasattr(msg, "reactions") or not msg.reactions:
        return None
    result = []
    for r in msg.reactions.results:
        result.append({
            "emoticon": getattr(r.reaction, "emoticon", None),
            "count": r.count,
        })
    return result


async def resolve_group(client, target):
    logger.info("Resolving: %s", target)
    try:
        entity = await client.get_entity(target)
        logger.info("Found: %s (id=%s)", getattr(entity, "title", target), entity.id)
        return entity
    except ValueError:
        pass
    async for dialog in client.iter_dialogs():
        if dialog.name and target.lower() in dialog.name.lower():
            logger.info("Found by name: %s (id=%s)", dialog.name, dialog.id)
            return dialog.entity
    raise SystemExit(f"Group not found: {target}")


async def dump_messages(client, entity, output_path, download_media=False, media_dir=None):
    total = 0
    start = datetime.now()
    with open(output_path, "w", encoding="utf-8") as f:
        async for msg in client.iter_messages(entity, limit=None, wait_time=0.5):
            try:
                record = serialise_message(msg)
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total += 1
                if download_media and msg.media and media_dir:
                    try:
                        await msg.download_media(file=media_dir, thumb=-1)
                    except Exception:
                        pass
                if total % 500 == 0:
                    elapsed = (datetime.now() - start).total_seconds()
                    logger.info("Dumped %d (%.0f msg/s) ... %s", total,
                                total / elapsed if elapsed else 0,
                                msg.date.strftime("%Y-%m-%d %H:%M"))
            except errors.FloodWaitError as e:
                logger.warning("Flood wait %ds", e.seconds)
                await asyncio.sleep(e.seconds)
    elapsed = (datetime.now() - start).total_seconds()
    logger.info("Done: %d messages -> %s (%.1fs, %.0f msg/s)",
                total, output_path, elapsed, total / elapsed if elapsed else 0)
    return total


# --- Auth (non-interactive via env vars) ----------------------------------

async def do_auth(client: TelegramClient, args) -> None:
    await client.connect()

    if await client.is_user_authorized():
        logger.info("Session valid, skipping login.")
        return

    phone = args.phone or os.environ.get("TELEGRAM_PHONE", "")
    if not phone:
        phone = input("Phone (+8613800138000): ")

    code = args.code or os.environ.get("TELEGRAM_CODE", "")
    hash_file = Path(str(client.session.filename) + ".hash")

    if not code:
        # Send code, save phone_code_hash to file
        sent = await client.send_code_request(phone)
        phash = sent.phone_code_hash
        hash_file.write_text(phash)
        logger.info("Code sent to %s (hash saved)", phone)
        logger.info("Run again with --phone and --code")
        await client.disconnect()
        sys.exit(0)

    # Read phone_code_hash from file
    if hash_file.exists():
        phash = hash_file.read_text().strip()
        hash_file.unlink()
        logger.info("Read phone_code_hash from file")
    else:
        # Fallback: send a new code request to get the hash
        sent = await client.send_code_request(phone)
        phash = sent.phone_code_hash
        logger.info("Sent new code (hash from new request)")

    logger.info("Signing in...")
    password = args.password or os.environ.get("TELEGRAM_PASSWORD", "")

    try:
        await client.sign_in(phone, code, password=password or None, phone_code_hash=phash)
        logger.info("Login successful!")
    except errors.SessionPasswordNeededError:
        if not password:
            password = getpass.getpass("2FA password: ")
        await client.sign_in(password=password, phone_code_hash=phash)
        logger.info("Login with 2FA successful!")
    except errors.PhoneCodeExpiredError:
        raise SystemExit("Code expired. Run again.")
    except errors.PhoneCodeInvalidError:
        raise SystemExit("Invalid code.")


# --- Main -----------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Dump Telegram group messages")
    p.add_argument("--group", "-g", help="Group username/ID")
    p.add_argument("--output", "-o", help="Output file")
    p.add_argument("--download-media", action="store_true")
    p.add_argument("--media-dir", help="Directory for media")
    p.add_argument("--phone", help="Phone (+86138...)")
    p.add_argument("--code", help="Verification code")
    p.add_argument("--password", help="2FA password")
    p.add_argument("--new-session", action="store_true")
    args = p.parse_args()

    api_id = int(env_or_raise("API_ID"))
    api_hash = env_or_raise("API_HASH")
    target = args.group or env_or_raise("TARGET_GROUP")
    od = Path(os.environ.get("OUTPUT_DIR", "./output"))
    od.mkdir(parents=True, exist_ok=True)

    sn = target.lstrip("@").replace("/", "_").replace("\\", "_").replace(":", "_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(args.output) if args.output else (od / f"{sn}_{ts}.jsonl")

    sp = od / "telethon_session"
    if args.new_session:
        for f in od.glob("telethon_session*"):
            f.unlink()
            logger.info("Deleted: %s", f)

    md = None
    if args.download_media:
        md = Path(args.media_dir) if args.media_dir else (od / "media")
        md.mkdir(parents=True, exist_ok=True)

    logger.info("Target: %s", target)
    logger.info("Output: %s", output_path)

    async def _run():
        client = TelegramClient(str(sp), api_id, api_hash)
        await do_auth(client, args)
        async with client:
            entity = await resolve_group(client, target)
            await dump_messages(client, entity, output_path,
                                download_media=args.download_media, media_dir=md)

    asyncio.run(_run())


if __name__ == "__main__":
    main()
