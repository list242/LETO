# bot.py
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers.button_handler import (
    start_handler, faq_handler, help_handler,
    callback_handler, boat_handler, register_admin, conv_handler, cancel
)
import os
from handlers.button_handler import start_quiz, handle_quiz_answer
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bookings_storage import delete_booking
from handlers.utils import load_admins
from telegram.ext import MessageHandler, filters
TOKEN = "7933616069:AAE1rIpYDIehi3h5gYFU7UQizeYhCifbFRk"
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден")

application = Application.builder().token(TOKEN).build()

# Новый обработчик одобрения/отклонения заявок
async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    action, user_id_str = data.split("-")
    user_id = int(user_id_str)
    admins = load_admins()

    if update.effective_user.id not in admins:
        await query.edit_message_text("❌ У вас нет прав для этого действия.")
        return
    message_id = context.bot_data.get(f"booking_msg_id-{user_id}")

    if action == "approve":
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Ваша бронь подтверждена администратором."
        )
        await query.edit_message_text("✅ Заявка одобрена.")
    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Ваша бронь отклонена администратором."
        )
        await query.edit_message_text("❌ Заявка отклонена.")
        delete_booking(user_id)


    context.bot_data.pop(f"pending-{user_id}", None)
    context.bot_data.pop(f"booking_msg_id-{user_id}", None)

async def get_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo = update.message.photo[-1]  # Самое большое разрешение
        await update.message.reply_text(f"📎 File ID: {photo.file_id}")

application.add_handler(MessageHandler(filters.PHOTO, get_file_id))
application.add_handler(start_handler)
application.add_handler(boat_handler)
application.add_handler(faq_handler)
application.add_handler(help_handler)
application.add_handler(CommandHandler("register", register_admin))
application.add_handler(conv_handler)
application.add_handler(CommandHandler("start_quiz", start_quiz))
application.add_handler(CallbackQueryHandler(start_quiz, pattern="^start_quiz$"))
application.add_handler(CallbackQueryHandler(handle_quiz_answer, pattern=r"^quiz_\d+_\d+$"))
application.add_handler(CallbackQueryHandler(handle_approval, pattern=r"^(approve|reject)-\d+$"))
application.add_handler(callback_handler)  # <-- обязательно в самом конце