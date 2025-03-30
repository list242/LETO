# handlers/menu_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚤 Выбор лодки", callback_data="select_boat")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
        [InlineKeyboardButton("❓ Частые вопросы", callback_data="faq")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("👋 Добро пожаловать! Выберите один из пунктов ниже:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("👋 Добро пожаловать! Выберите один из пунктов ниже:", reply_markup=reply_markup)

async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📌 Частые вопросы:\n"
        "- 📅 Можно ли перенести бронь?\n"
        "- ⚓ Какие условия аренды?\n"
        "- 👶 Есть ли ограничения по возрасту?\n"
        "🔙 Для возврата в меню нажмите кнопку .",
        reply_markup=reply_markup
    )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "❓ Раздел помощи:\n"
        "1️⃣ Как забронировать лодку?\n"
        "2️⃣ Какие есть правила пользования лодкой?\n"
        "3️⃣ Как отменить бронь?\n"
        "🔙 Для возврата в меню нажмите кнопку ниже.",
        reply_markup=reply_markup
    )

# Регистрация обработчиков
start_handler = CommandHandler("start", start)
faq_handler = CallbackQueryHandler(faq_handler, pattern="^faq$")
help_handler = CallbackQueryHandler(help_handler, pattern="^help$")
back_handler = CallbackQueryHandler(start, pattern="^back_to_start$")