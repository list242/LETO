# handlers/faq_help_handlers/faq_handler.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes

async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Загрузка...", show_alert=False)
    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    faq_text = (
        "📌 Частые вопросы:\n"
        "- 📅 Можно ли перенести бронь?\n"
        "- ⚓ Какие условия аренды?\n"
        "- 👶 Есть ли ограничения по возрасту?\n"
        "🔙 Для возврата в меню нажмите кнопку ниже."
    )
    await query.edit_message_text(faq_text, reply_markup=reply_markup)

# Экспортируем обработчик
# faq_handler = CallbackQueryHandler(faq_handler, pattern="^faq$")