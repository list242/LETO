# bot.py
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers.button_handler import (
    start_handler, faq_handler, help_handler,
    callback_handler, boat_handler, register_admin, conv_handler, cancel
)
from handlers.button_handler import start_quiz, handle_quiz_answer

import os
from dotenv import load_dotenv

# === Загрузка .env переменных ===
load_dotenv()

MODE = os.getenv("MODE", "polling")  # polling или webhook
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # используется для webhook
PORT = int(os.getenv("PORT", 8080))
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env")

application = Application.builder().token(TOKEN).build()

# === Обработчики ===
application.add_handler(start_handler)
application.add_handler(boat_handler)
application.add_handler(faq_handler)
application.add_handler(help_handler)
application.add_handler(CommandHandler("register", register_admin))
application.add_handler(conv_handler)
application.add_handler(CommandHandler("start_quiz", start_quiz))
application.add_handler(CallbackQueryHandler(start_quiz, pattern="^start_quiz$"))
application.add_handler(CallbackQueryHandler(handle_quiz_answer, pattern=r"^quiz_\d+_\d+$"))
application.add_handler(callback_handler)  # обязательно в конце

# === Запуск ===
if __name__ == "__main__":
    if MODE == "polling":
        print("🚀 Бот запускается в режиме POLLING")
        application.run_polling()
    else:
        print(f"🌐 Бот запускается в режиме WEBHOOK → {WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL
        )
