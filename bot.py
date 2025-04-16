# bot.py
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers.button_handler import (
    start_handler, faq_handler, help_handler,
    callback_handler, boat_handler, register_admin, conv_handler, cancel
)
import os
from handlers.button_handler import start_quiz, handle_quiz_answer
TOKEN = "7933616069:AAE1rIpYDIehi3h5gYFU7UQizeYhCifbFRk"
#TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден")

application = Application.builder().token(TOKEN).build()

# Обработчики
application.add_handler(start_handler)
application.add_handler(boat_handler)
application.add_handler(faq_handler)
application.add_handler(help_handler)
#application.add_handler(back_handler)
application.add_handler(CommandHandler("register", register_admin))
application.add_handler(conv_handler)
application.add_handler(CommandHandler("start_quiz", start_quiz))
application.add_handler(CallbackQueryHandler(start_quiz, pattern="^start_quiz$"))
application.add_handler(CallbackQueryHandler(handle_quiz_answer, pattern=r"^quiz_\d+_\d+$"))
application.add_handler(callback_handler)  # <-- обязательно в самом конце
