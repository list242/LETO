# handlers/faq_help_handlers/help_handler.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Загрузка...", show_alert=False)
    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    help_text = (
        "❓ Раздел помощи:\n"
        "1️⃣ Как забронировать лодку?\n"
        "2️⃣ Какие есть правила пользования лодкой?\n"
        "3️⃣ Как отменить бронь?\n"
        "🔙 Для возврата в меню нажмите кнопку ниже."
    )
    await query.edit_message_text(help_text, reply_markup=reply_markup)

# Экспортируем обработчик
# help_handler = CallbackQueryHandler(help_handler, pattern="^help$")