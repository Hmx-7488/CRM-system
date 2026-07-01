# Telegram Group Message Dumper

Pull all messages from a Telegram group chat. Two approaches:

| Script | Method | History | Live | Requires |
|--------|--------|---------|------|----------|
| `dump_messages.py` | Telethon (MTProto) | All messages | No | User account API credentials |
| `live_capture.py` | Bot API | From join point | Yes | Bot Token only |

---

## Setup

```powershell
pip install telethon python-telegram-bot
```

```powershell
copy .env.example .env
# Edit .env with your credentials
```

---

## 1. Dump historical messages (all messages, recommended)

This uses your personal Telegram account to pull the complete message history.

### Get credentials

1. Go to https://my.telegram.org/apps
2. Log in, create an app, copy `api_id` and `api_hash`
3. Fill them into `.env`

### Run

```powershell
$env:API_ID="12345678"
$env:API_HASH="abcdef1234567890abcdef1234567890"
$env:TARGET_GROUP="@your_group_username"

python dump_messages.py
```

First run will ask for your phone number and verification code (session is cached).

**Output**: `output/<group>_<timestamp>.jsonl` -- one JSON object per line.

### Options

```powershell
python dump_messages.py -g @other_group -o my_export.jsonl
python dump_messages.py --download-media --media-dir ./photos
python dump_messages.py -b 50   # smaller batch size if hitting rate limits
```

### JSON Output Format

Each line is a message:
```json
{
  "id": 12345,
  "date": "2025-06-15T08:30:00+00:00",
  "text": "Hello everyone!",
  "sender": {"id": 98765, "username": "alice", "first_name": "Alice", ...},
  "is_reply": false,
  "media": {"type": "photo", "id": 55555},
  "reactions": [{"emoticon": "?Y", "count": 3}],
  "views": 150,
  ...
}
```

---

## 2. Live capture (new messages only)


Uses your bot BlackBot to capture messages **going forward** in real time.

### Prerequisites

1. The bot MUST be added to the target group as **admin**
2. Bot privacy mode MUST be **disabled** (@BotFather -> /mybots -> Bot Settings -> Group Privacy -> Turn off)
3. Fill `TELEGRAM_BOT_TOKEN` in `.env`

### Run

```powershell
$env:TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."
python live_capture.py
```

Messages are written to `output/live_capture_<timestamp>.jsonl` as they arrive.

**Limitation**: Bot can only see messages sent after it joined the group. Use `dump_messages.py` for history.

---

## Merging data

If you run `dump_messages.py` first for history, then `live_capture.py` for ongoing capture:

```powershell
# Step 1: dump all historical messages
python dump_messages.py

# Step 2: start live capture (in a separate terminal)
python live_capture.py

# Later, concatenate:
Get-Content output\mygroup_*.jsonl | Sort-Object -Unique | Set-Content output\merged.jsonl
```

---

## Security notes

- `.env` is in `.gitignore` -- never commit your tokens
- The Telethon session file (`output/telethon_session.session`) contains your login -- keep it private
- Bot token has limited scope; Telethon session has full account access
