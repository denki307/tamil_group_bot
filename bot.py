
import os
from telegram import Update, ChatPermissions
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

mongo = MongoClient(MONGO_URL)
db = mongo["tamilbot"]
memory = db["chat_memory"]
warns = db["warns"]

def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 Tamil Learning Group Bot Ready!")

def warn(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        return
    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    key = {"chat": chat_id, "user": user.id}
    data = warns.find_one(key) or {"count": 0}
    count = data["count"] + 1
    warns.update_one(key, {"$set": {"count": count}}, upsert=True)

    if count >= 3:
        context.bot.restrict_chat_member(chat_id, user.id, ChatPermissions(can_send_messages=False))
        update.message.reply_text(f"🚫 {user.first_name} muted (3 warns)")
    else:
        update.message.reply_text(f"⚠️ Warn {count}/3")

def mute(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        update.message.reply_text("Reply panninaal dhaan mute panna mudiyum")
        return
    user = update.message.reply_to_message.from_user
    context.bot.restrict_chat_member(update.effective_chat.id, user.id, ChatPermissions(can_send_messages=False))
    update.message.reply_text(f"🔇 {user.first_name} muted")

def unmute(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        return
    user = update.message.reply_to_message.from_user
    context.bot.restrict_chat_member(update.effective_chat.id, user.id, ChatPermissions(can_send_messages=True))
    update.message.reply_text("✅ Unmuted")

def auto_delete(update: Update, context: CallbackContext):
    text = update.message.text.lower()
    if "http://" in text or "https://" in text or "t.me/" in text:
        update.message.delete()

def learning_chat(update: Update, context: CallbackContext):
    text = update.message.text.lower()
    if text.startswith("/"):
        return
    data = memory.find_one({"text": text})
    if data:
        update.message.reply_text(data["reply"])
    else:
        memory.insert_one({"text": text, "reply": text})

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("warn", warn))
    dp.add_handler(CommandHandler("mute", mute))
    dp.add_handler(CommandHandler("unmute", unmute))
    dp.add_handler(MessageHandler(Filters.text & Filters.group, auto_delete))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, learning_chat))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
