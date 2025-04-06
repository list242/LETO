import os
from telegram.ext import Application, CommandHandler
from handlers.button_handler import (
    start_handler, approve_handler, faq_handler, help_handler, back_handler,
    callback_handler, boat_handler, register_admin, conv_handler, cancel
)
from handlers.utils import load_admins
BOT_TOKEN = "7933616069:AAE1rIpYDIehi3h5gYFU7UQizeYhCifbFRk"
# === Telegram Setup ===
TOKEN = os.getenv("BOT_TOKEN")
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

# === Запуск бота (локально через polling) ===
if __name__ == '__main__':
    application.run_polling()
