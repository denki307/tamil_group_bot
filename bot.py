import os
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatPermissions
from pymongo import MongoClient
from replies import get_reply, BAD_WORDS

# ===== ENV =====
TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

# ===== DB =====
mongo = MongoClient(MONGO_URL)
db = mongo["tamilbot"]
memory = db["chat_memory"]

WARN_LIMIT = 3
WARN_DATA = {}
LAST_MESSAGES = {}

# ---------- HELPERS ----------
def is_admin(update, context):
    member = context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id
    )
    return member.status in ["administrator", "creator"]

# ---------- COMMANDS ----------
def start(update, context):
    update.message.reply_text(
        "🤖 Tamil Group Moderation Bot\n\n"
        "Admin Commands:\n"
        "/warn (reply)\n"
        "/mute (reply)\n"
        "/unmute (reply)\n"
        "/kick (reply)"
    )

def warn(update, context):
    if not is_admin(update, context):
        update.message.reply_text("❌ Admin only command")
        return

    if not update.message.reply_to_message:
        update.message.reply_text("⚠️ User message-ku reply pannunga")
        return

    user = update.message.reply_to_message.from_user
    uid = user.id

    WARN_DATA[uid] = WARN_DATA.get(uid, 0) + 1
    warns = WARN_DATA[uid]

    if warns >= WARN_LIMIT:
        until = datetime.now() + timedelta(minutes=10)
        context.bot.restrict_chat_member(
            update.effective_chat.id,
            uid,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        WARN_DATA[uid] = 0
        update.message.reply_text(
            f"🔇 {user.first_name} muted (3 warns)"
        )
    else:
        update.message.reply_text(
            f"⚠️ Warn {warns}/{WARN_LIMIT} for {user.first_name}"
        )

def unmute(update, context):
    if not is_admin(update, context):
        update.message.reply_text("❌ Admin only command")
        return

    if not update.message.reply_to_message:
        update.message.reply_text("⚠️ Reply to muted user")
        return

    uid = update.message.reply_to_message.from_user.id
    context.bot.restrict_chat_member(
        update.effective_chat.id,
        uid,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )
    update.message.reply_text("🔊 User unmuted")

def kick(update, context):
    if not is_admin(update, context):
        update.message.reply_text("❌ Admin only command")
        return

    if not update.message.reply_to_message:
        update.message.reply_text("⚠️ Reply to user")
        return

    uid = update.message.reply_to_message.from_user.id
    context.bot.kick_chat_member(update.effective_chat.id, uid)
    update.message.reply_text("👢 User kicked")

# ---------- AUTO MODERATION + LEARNING ----------
def auto_moderate(update, context):
    msg = update.message
    uid = msg.from_user.id
    text = msg.text.lower()

    # Bad word filter
    for w in BAD_WORDS:
        if w in text:
            msg.delete()
            return

    # Spam detection (same message)
    if uid in LAST_MESSAGES and LAST_MESSAGES[uid] == text:
        msg.delete()
        return

    LAST_MESSAGES[uid] = text

    # ===== LEARNING CHAT =====
    data = memory.find_one({"text": text})
    if data:
        msg.reply_text(data["reply"])
    else:
        memory.insert_one({
            "text": text,
            "reply": get_reply(),
            "count": 1
        })

# ---------- MAIN ----------
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("warn", warn))
    dp.add_handler(CommandHandler("unmute", unmute))
    dp.add_handler(CommandHandler("kick", kick))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, auto_moderate))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
