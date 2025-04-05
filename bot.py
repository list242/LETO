import os
from telegram.ext import Application, CommandHandler
from handlers.button_handler import (
    start_handler, approve_handler, faq_handler, help_handler, back_handler,
    callback_handler, boat_handler, register_admin, conv_handler, cancel
)
from handlers.utils import load_admins

# === Telegram Setup ===
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

application = Application.builder().token(TOKEN).build()

# === Обработчики ===
application.add_handler(start_handler)
application.add_handler(boat_handler)
application.add_handler(callback_handler)
application.add_handler(faq_handler)
application.add_handler(help_handler)
application.add_handler(back_handler)
application.add_handler(CommandHandler("register", register_admin))
application.add_handler(conv_handler)
application.add_handler(approve_handler)

# === Запуск через встроенный run_webhook с правильным webhook_path ===
if __name__ == '__main__':
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/telegram",
        webhook_path="/telegram"
    )
