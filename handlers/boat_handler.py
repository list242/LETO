# boat_handler.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram import Update

# Функция для отображения кнопок лодок
async def choose_boat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Синяя лодка", callback_data="blue")],
        [InlineKeyboardButton("Красная лодка", callback_data="red")],
        [InlineKeyboardButton("Белая лодка", callback_data="white")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Выберите лодку:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.edit_message_text("Выберите лодку:", reply_markup=reply_markup)

# Экспортируем обработчик
boat_handler = CallbackQueryHandler(choose_boat, pattern="^select_boat$")