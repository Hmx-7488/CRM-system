# Telegram 群组消息导出工具

从 Telegram 群聊中拉取所有消息。两种方法：

| 脚本 | 方法 | 历史消息 | 实时消息 | 需要 |
|--------|--------|---------|------|----------|
| `dump_messages.py` | Telethon (MTProto) | 所有消息 | 否 | 用户账户 API 凭据 |
| `live_capture.py` | Bot API | 从加入点开始 | 是 | 仅需 Bot Token |

---

## 设置

```powershell
pip install telethon python-telegram-bot
```

```powershell
copy .env.example .env
# 编辑 .env 文件，填入你的凭据
```

---

## 1. 导出历史消息（所有消息，推荐）

此方法使用你的个人 Telegram 账户拉取完整的消息历史记录。

### 获取凭据

1. 访问 https://my.telegram.org/apps
2. 登录，创建一个应用，复制 `api_id` 和 `api_hash`
3. 将它们填入 `.env` 文件

### 运行

```powershell
$env:API_ID="12345678"
$env:API_HASH="abcdef1234567890abcdef1234567890"
$env:TARGET_GROUP="@your_group_username"

python dump_messages.py
```

首次运行会要求输入你的手机号码和验证码（会话会被缓存）。

**输出**：`output/<group>_<timestamp>.jsonl` -- 每行一个 JSON 对象。

### 选项

```powershell
python dump_messages.py -g @other_group -o my_export.jsonl
python dump_messages.py --download-media --media-dir ./photos
python dump_messages.py -b 50   # 如果遇到速率限制，减小批次大小
```

### JSON 输出格式

每行一条消息：
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

## 2. 实时捕获（仅新消息）


使用你的 bot BlackBot **实时捕获** 消息。

### 前提条件

1. 机器人**必须**以**管理员**身份添加到目标群组
2. 机器人的隐私模式**必须**设置为**禁用**（@BotFather -> /mybots -> Bot Settings -> Group Privacy -> 关闭）
3. 在 `.env` 文件中填入 `TELEGRAM_BOT_TOKEN`

### 运行

```powershell
$env:TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."
python live_capture.py
```

消息会在到达时写入 `output/live_capture_<timestamp>.jsonl` 文件。

**限制**：机器人只能看到它加入群组后发送的消息。要获取历史记录，请使用 `dump_messages.py`。

---

## 合并数据

如果你先运行 `dump_messages.py` 获取历史记录，然后运行 `live_capture.py` 进行实时捕获：

```powershell
# 步骤 1：导出所有历史消息
python dump_messages.py

# 步骤 2：启动实时捕获（在另一个终端中）
python live_capture.py

# 之后，合并文件：
Get-Content output\mygroup_*.jsonl | Sort-Object -Unique | Set-Content output\merged.jsonl
```

---

## 安全注意事项

- `.env` 文件已添加到 `.gitignore` -- 切勿提交你的 token
- Telethon 会话文件（`output/telethon_session.session`）包含你的登录信息 -- 请妥善保管
- Bot token 权限有限；Telethon 会话具有完整的账户访问权限