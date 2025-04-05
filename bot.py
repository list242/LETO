import os
from telegram.ext import Application, CommandHandler
from handlers.button_handler import (
    start_handler, approve_handler, faq_handler, help_handler, back_handler,
    callback_handler, boat_handler, register_admin, conv_handler, cancel
)
from handlers.utils import load_admins
from aiohttp import web

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
async def yclients_disconnect(request):
    try:
        data = await request.json()
        print("❌ Отключение интеграции от YCLIENTS:", data)

        # Можно добавить отправку в Telegram:
        # await application.bot.send_message(chat_id=АДМИН_ID, text="❌ Интеграция отключена!")

        return web.json_response({"status": "ok"})
    except Exception as e:
        print("⚠️ Ошибка при disconnect webhook:", e)
        return web.json_response({"error": str(e)}, status=500)

app = web.Application()
app.router.add_post("/yclients-disconnect", yclients_disconnect)


# === Запуск через встроенный run_webhook с правильным webhook_path ===
if __name__ == '__main__':
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/telegram",
        webhook_path="/telegram"
    )
