import os
import sys
from datetime import datetime, timedelta
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
from telegram import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
)
from pymongo import MongoClient
from replies import get_reply, BAD_WORDS
import openai

# ===== ENV =====
TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
OWNER_ID = int(os.getenv("OWNER_ID", "8516457288"))
OPENAI_KEY = os.getenv("OPENAI_KEY")
openai.api_key = OPENAI_KEY

# ===== DB =====
mongo = MongoClient(MONGO_URL)
db = mongo["tamilbot"]

memory = db["chat_memory"]
sudo_db = db["sudo_users"]
gban_db = db["global_bans"]

# ===== CONST =====
WARN_LIMIT = 3
WARN_DATA = {}
LAST_MESSAGES = {}

# ---------- HELPERS ----------
def is_admin(update, context):
    member = context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id,
    )
    return member.status in ("administrator", "creator")

def is_sudo(user_id):
    return user_id == OWNER_ID or sudo_db.find_one({"user_id": user_id})

# ---------- START ----------
def start(update, context):
    keyboard = [
        [InlineKeyboardButton("💬 SUPPORT GROUP", url="https://t.me/MUSIC_BOT_WORLD")],
        [InlineKeyboardButton("📢 SUPPORT CHANNEL", url="https://t.me/MUSIC_BOT_TEAM")],
        [
            InlineKeyboardButton("📖 HELP", callback_data="help"),
            InlineKeyboardButton("👑 OWNER", url="https://t.me/DENKI1234"),
        ],
    ]

    update.message.reply_photo(
        photo="https://graph.org/file/5edba62fe35cba67f3ad9-7ae56f4f2bd098647d.jpg",
        caption=(
            "🤖 Tamil Group Moderation Bot\n\n"
            "• Auto moderation\n"
            "• Warn / Mute system\n"
            "• Learning auto reply\n\n"
            "_Use in groups & make me admin_ 😎"
        ),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ---------- HELP MENU ----------
def help_menu(update, context):
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("📢 BROADCAST", callback_data="broadcast")],
        [InlineKeyboardButton("🤧 GBAN", callback_data="gban")],
        [InlineKeyboardButton("📝 INFO", callback_data="info")],
        [InlineKeyboardButton("🥀 SUDO", callback_data="sudo")],
    ]

    query.edit_message_caption(
        caption="📖 *Help Menu*\n\nChoose a category:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ---------- HELP PAGES ----------
def help_pages(update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="help")]
    ])

    if data == "broadcast":
        text = (
            "📢 *BROADCAST*\n\n"
            "/broadcast <message>\n\n"
            "_Send message to all served chats_\n"
            "*SUDO only*"
        )
    elif data == "gban":
        text = (
            "🤧 *GLOBAL BAN*\n\n"
            "/gban [reply/user_id]\n"
            "/ungban [reply/user_id]\n"
            "/gbannedusers\n\n"
            "*SUDO only*"
        )
    elif data == "info":
        text = "📝 *INFO*\n\n/id – Get chat or user ID"
    elif data == "sudo":
        text = (
            "🥀 *SUDO & OWNER*\n\n"
            "/addsudo [reply/user_id]\n"
            "/delsudo [reply/user_id]\n"
            "/sudolist\n"
            "/restart – Restart bot"
        )
    else:
        return

    query.edit_message_caption(
        caption=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=back_keyboard
    )

# ---------- WARN / MUTE ----------
def warn(update, context):
    if not is_admin(update, context):
        return

    if not update.message.reply_to_message:
        update.message.reply_text("Reply to a user.")
        return

    user = update.message.reply_to_message.from_user
    uid = user.id

    WARN_DATA[uid] = WARN_DATA.get(uid, 0) + 1

    if WARN_DATA[uid] >= WARN_LIMIT:
        context.bot.restrict_chat_member(
            update.effective_chat.id,
            uid,
            ChatPermissions(can_send_messages=False),
            until_date=datetime.now() + timedelta(minutes=10),
        )
        WARN_DATA[uid] = 0
        update.message.reply_text(f"🔇 {user.first_name} muted (3 warns)")
    else:
        update.message.reply_text(f"⚠️ Warn {WARN_DATA[uid]}/{WARN_LIMIT}")

def unmute(update, context):
    if not is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return

    uid = update.message.reply_to_message.from_user.id
    context.bot.restrict_chat_member(
        update.effective_chat.id,
        uid,
        ChatPermissions(can_send_messages=True),
    )
    update.message.reply_text("🔊 User unmuted")

# ---------- INFO ----------
def get_id(update, context):
    if update.message.reply_to_message:
        update.message.reply_text(
            f"👤 User ID: `{update.message.reply_to_message.from_user.id}`",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        update.message.reply_text(
            f"💬 Chat ID: `{update.effective_chat.id}`",
            parse_mode=ParseMode.MARKDOWN,
        )

# ---------- SUDO ----------
def addsudo(update, context):
    if update.effective_user.id != OWNER_ID:
        return
    if not update.message.reply_to_message:
        return
    uid = update.message.reply_to_message.from_user.id
    sudo_db.update_one({"user_id": uid}, {"$set": {"user_id": uid}}, upsert=True)
    update.message.reply_text("✅ Sudo added")

def delsudo(update, context):
    if update.effective_user.id != OWNER_ID:
        return
    if not update.message.reply_to_message:
        return
    uid = update.message.reply_to_message.from_user.id
    sudo_db.delete_one({"user_id": uid})
    update.message.reply_text("❌ Sudo removed")

def sudolist(update, context):
    sudos = sudo_db.find()
    text = "🥀 *Sudo Users*\n\n"
    for s in sudos:
        text += f"`{s['user_id']}`\n"
    update.message.reply_text(text or "No sudos", parse_mode=ParseMode.MARKDOWN)

# ---------- GBAN ----------
def gban(update, context):
    if not is_sudo(update.effective_user.id):
        return
    if not update.message.reply_to_message:
        return
    uid = update.message.reply_to_message.from_user.id
    gban_db.update_one({"user_id": uid}, {"$set": {"user_id": uid}}, upsert=True)
    update.message.reply_text("🚫 User globally banned")

def ungban(update, context):
    if not is_sudo(update.effective_user.id):
        return
    if not update.message.reply_to_message:
        return
    uid = update.message.reply_to_message.from_user.id
    gban_db.delete_one({"user_id": uid})
    update.message.reply_text("✅ User globally unbanned")

def gbannedusers(update, context):
    bans = gban_db.find()
    text = "🚫 *Globally Banned Users*\n\n"
    for b in bans:
        text += f"`{b['user_id']}`\n"
    update.message.reply_text(text or "No bans", parse_mode=ParseMode.MARKDOWN)

# ---------- AUTO MODERATION + AI ----------
def auto_moderate(update, context):
    uid = update.message.from_user.id
    text = update.message.text.lower()

    # Delete if globally banned
    if gban_db.find_one({"user_id": uid}):
        update.message.delete()
        return

    # Delete if contains bad words
    for w in BAD_WORDS:
        if w in text:
            update.message.delete()
            return

    # Delete if repeated message
    if LAST_MESSAGES.get(uid) == text:
        update.message.delete()
        return

    LAST_MESSAGES[uid] = text

    # AI Reply
    reply_text = get_reply(text)
    update.message.reply_text(reply_text)


# ---------- BROADCAST ----------
def broadcast(update, context):
    if not is_sudo(update.effective_user.id):
        update.message.reply_text("❌ SUDO only command")
        return
    if not context.args:
        update.message.reply_text("Usage:\n/broadcast <message>")
        return
    msg = " ".join(context.args)
    chats = memory.distinct("chat_id")
    sent = 0
    failed = 0
    for chat_id in chats:
        try:
            context.bot.send_message(chat_id, msg)
            sent += 1
        except:
            failed += 1
    update.message.reply_text(f"📢 Broadcast finished!\n✅ Sent: {sent}\n❌ Failed: {failed}")

# ---------- RESTART ----------
def restart(update, context):
    if not is_sudo(update.effective_user.id):
        return
    update.message.reply_text("♻️ Restarting bot...")
    os.execl(sys.executable, sys.executable, *sys.argv)

# ---------- MAIN ----------
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("warn", warn))
    dp.add_handler(CommandHandler("unmute", unmute))
    dp.add_handler(CommandHandler("id", get_id))
    dp.add_handler(CommandHandler("addsudo", addsudo))
    dp.add_handler(CommandHandler("delsudo", delsudo))
    dp.add_handler(CommandHandler("sudolist", sudolist))
    dp.add_handler(CommandHandler("gban", gban))
    dp.add_handler(CommandHandler("ungban", ungban))
    dp.add_handler(CommandHandler("gbannedusers", gbannedusers))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    dp.add_handler(CommandHandler("restart", restart))

    dp.add_handler(CallbackQueryHandler(help_menu, pattern="help"))
    dp.add_handler(CallbackQueryHandler(help_pages))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, auto_moderate))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

