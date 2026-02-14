import openai
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ===== CONFIG =====
TELEGRAM_TOKEN = "8236839551:AAH-QOFcpOkAQd_U_YrNvPbZmex3mIBIHNA"
OPENAI_API_KEY = "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"

openai.api_key = OPENAI_API_KEY
# ==================


async def ai_reply(text):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": text}],
    )
    return response["choices"][0]["message"]["content"]


# ===== START COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("🤖 About", callback_data="about")],
        [InlineKeyboardButton("❌ Close", callback_data="delete")],
    ]

    with open("start.jpg", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="🔥 Welcome!\nI am an AI assistant.\nSend me any message.",
            reply_markup=InlineKeyboardMarkup(buttons),
        )


# ===== NORMAL MESSAGE =====
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text

    answer = await ai_reply(msg)

    buttons = [
        [
            InlineKeyboardButton("🔁 Regenerate", callback_data=f"regen|{msg}"),
            InlineKeyboardButton("✂️ Shorten", callback_data=f"short|{msg}"),
        ],
        [InlineKeyboardButton("🧹 Delete", callback_data="delete")],
    ]

    await update.message.reply_text(
        answer, reply_markup=InlineKeyboardMarkup(buttons)
    )


# ===== BUTTON HANDLE =====
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "delete":
        await query.message.delete()
        return

    if data == "about":
        await query.answer("AI powered reply bot 🚀", show_alert=True)
        return

    action, text = data.split("|", 1)

    if action == "regen":
        new_answer = await ai_reply(text)
    else:
        new_answer = await ai_reply("short answer: " + text)

    buttons = [
        [
            InlineKeyboardButton("🔁 Regenerate", callback_data=f"regen|{text}"),
            InlineKeyboardButton("✂️ Shorten", callback_data=f"short|{text}"),
        ],
        [InlineKeyboardButton("🧹 Delete", callback_data="delete")],
    ]

    await query.message.edit_text(
        new_answer, reply_markup=InlineKeyboardMarkup(buttons)
    )


# ===== RUN =====
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(button_click))

print("Bot running with START IMAGE...")
app.run_polling()
