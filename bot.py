# bot.py
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers.button_handler import (
    start_handler, approve_handler, faq_handler, help_handler, back_handler,
    callback_handler, boat_handler, register_admin, conv_handler, cancel
)
import os
from handlers.button_handler import start_quiz, handle_quiz_answer
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден")

application = Application.builder().token(TOKEN).build()

# Обработчики
application.add_handler(start_handler)
application.add_handler(boat_handler)
application.add_handler(callback_handler)
application.add_handler(faq_handler)
application.add_handler(help_handler)
application.add_handler(back_handler)
application.add_handler(CommandHandler("register", register_admin))
application.add_handler(conv_handler)
application.add_handler(approve_handler)
application.add_handler(CommandHandler("start_quiz", start_quiz))
application.add_handler(CallbackQueryHandler(handle_quiz_answer, pattern=r"^quiz_\d+_\d+$"))
