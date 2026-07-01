"""A practical Telegram Bot demo using python-telegram-bot v22+.

Features demonstrated:
  - /start — welcome with inline keyboard
  - /help  — list commands
  - /echo  — repeat user text
  - /caps  — convert text to uppercase
  - Inline keyboard callbacks
  - Conversation flow (name registration)
  - Error handling
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes,
    filters,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
ASK_NAME, ASK_AGE = range(2)

# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with an inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("📖 查看帮助", callback_data="help")],
        [
            InlineKeyboardButton("🔤 /caps 示例", callback_data="caps_demo"),
            InlineKeyboardButton("🔁 /echo 示例", callback_data="echo_demo"),
        ],
        [InlineKeyboardButton("📝 注册名字", callback_data="register")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 你好！我是 DemoBot。\n\n"
        "你可以直接发消息给我，或者点击下面的按钮：",
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List available commands."""
    text = (
        "📋 **可用命令**\n\n"
        "/start — 开始\n"
        "/help — 帮助\n"
        "/echo <文字> — 复读你的消息\n"
        "/caps <文字> — 转为大写\n"
        "/register — 注册你的名字（多步对话）\n"
        "/cancel — 取消当前操作"
    )
    await update.message.reply_text(text)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo back whatever the user said after /echo."""
    args = " ".join(context.args) if context.args else None
    if not args:
        await update.message.reply_text("用法：/echo <你想说的话>")
        return
    await update.message.reply_text(f"🦜 {args}")


async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Convert user text to uppercase."""
    args = " ".join(context.args) if context.args else None
    if not args:
        await update.message.reply_text("用法：/caps <文字>")
        return
    await update.message.reply_text(args.upper())


# ---------------------------------------------------------------------------
# Inline keyboard callbacks
# ---------------------------------------------------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all inline keyboard button presses."""
    query = update.callback_query
    await query.answer()  # acknowledge the button press

    data = query.data

    if data == "help":
        await query.edit_message_text(
            "📋 **可用命令**\n\n"
            "/start /help /echo /caps /register /cancel"
        )

    elif data == "echo_demo":
        await query.edit_message_text(
            "🔁 试试发送：\n`/echo Hello, Telegram!`"
        )

    elif data == "caps_demo":
        await query.edit_message_text(
            "🔤 试试发送：\n`/caps hello world`"
        )

    elif data == "register":
        await query.edit_message_text(
            "📝 请输入 /register 开始注册流程～"
        )

    else:
        await query.edit_message_text(f"未知按钮：{data}")


# ---------------------------------------------------------------------------
# Conversation: name registration
# ---------------------------------------------------------------------------
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration conversation — ask for name."""
    await update.message.reply_text("你叫什么名字？\n(输入 /cancel 取消)")
    return ASK_NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive name, then ask for age."""
    context.user_data["name"] = update.message.text
    await update.message.reply_text(f"好的 {update.message.text}，你多大了？")
    return ASK_AGE


async def register_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive age and finish registration."""
    try:
        age = int(update.message.text)
    except ValueError:
        await update.message.reply_text("请输入一个数字年龄。")
        return ASK_AGE

    name = context.user_data.get("name", "未知")
    await update.message.reply_text(f"✅ 注册完成！\n\n👤 {name}\n🎂 {age} 岁")
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("❌ 已取消。")
    context.user_data.clear()
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Fallback: handle any text message
# ---------------------------------------------------------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo back any plain text message."""
    await update.message.reply_text(f"收到：「{update.message.text}」\n\n试试 /help ？")


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors."""
    logger.error("Exception while handling update:", exc_info=context.error)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    """Build and run the bot."""
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ 请设置环境变量 TELEGRAM_BOT_TOKEN，或直接修改 TOKEN 变量。")
        print("   在 @BotFather 创建 Bot 后获取 Token。")
        return

    app = Application.builder().token(TOKEN).build()

    # Conversation handler — must be added before the generic MessageHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_age)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("caps", caps))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    print("🤖 Bot 已启动，按 Ctrl+C 停止...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
