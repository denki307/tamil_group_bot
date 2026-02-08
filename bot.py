import os
import re
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatPermissions
from replies import get_reply, BAD_WORDS

TOKEN = os.getenv("BOT_TOKEN")

WARN_LIMIT = 3
WARN_DATA = {}
LAST_MESSAGES = {}

def is_admin(update, context):
    member = context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id
    )
    return member.status in ["administrator", "creator"]

def contains_link(text):
    return re.search(r"(http://|https://|www\.|t\.me/)", text) is not None

def start(update, context):
    update.message.reply_text("🤖 Tamil Group Moderation Bot")

def warn(update, context):
    if not is_admin(update, context): return
    if not update.message.reply_to_message: return
    uid = update.message.reply_to_message.from_user.id
    WARN_DATA[uid] = WARN_DATA.get(uid, 0) + 1
    if WARN_DATA[uid] >= WARN_LIMIT:
        until = datetime.now() + timedelta(minutes=10)
        context.bot.restrict_chat_member(
            update.effective_chat.id,
            uid,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        WARN_DATA[uid] = 0
        update.message.reply_text("🔇 Auto muted (3 warns)")

def unmute(update, context):
    if not is_admin(update, context): return
    if not update.message.reply_to_message: return
    uid = update.message.reply_to_message.from_user.id
    context.bot.restrict_chat_member(
        update.effective_chat.id,
        uid,
        permissions=ChatPermissions(can_send_messages=True)
    )
    update.message.reply_text("🔊 Unmuted")

def kick(update, context):
    if not is_admin(update, context): return
    if not update.message.reply_to_message: return
    uid = update.message.reply_to_message.from_user.id
    context.bot.kick_chat_member(update.effective_chat.id, uid)

def auto_mod(update, context):
    msg = update.message
    text = msg.text.lower()
    if contains_link(text):
        msg.delete(); return
    for w in BAD_WORDS:
        if w in text:
            msg.delete(); return
    msg.reply_text(get_reply())

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("warn", warn))
    dp.add_handler(CommandHandler("unmute", unmute))
    dp.add_handler(CommandHandler("kick", kick))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, auto_mod))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
