import os
from telegram.ext import Application, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
from aiohttp import web
from handlers.button_handler import (
    start_handler, approve_handler, faq_handler, help_handler, back_handler,
    callback_handler, boat_handler, register_admin, conv_handler, cancel
)
from handlers.utils import load_admins

# === Telegram Setup ===
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
application = Application.builder().token(TOKEN).build()

# === Обработчики ===
application.add_handler(CommandHandler("start", start_handler.callback))
application.add_handler(start_handler)
application.add_handler(boat_handler)
application.add_handler(callback_handler)
application.add_handler(faq_handler)
application.add_handler(help_handler)
application.add_handler(back_handler)
application.add_handler(CommandHandler("register", register_admin))
application.add_handler(conv_handler)
application.add_handler(approve_handler)

# === Yclients webhook ===
async def yclients_webhook(request):
    try:
        data = await request.json()
        print("📩 Webhook от Yclients:", data)
        return web.json_response({"status": "ok"})
    except Exception as e:
        print("❌ Ошибка при обработке webhook:", e)
        return web.json_response({"error": str(e)}, status=500)

# === Aiohttp Server ===
app = web.Application()
app.router.add_post("/yclients-webhook", yclients_webhook)

async def on_startup(app):
    await application.initialize()
    print(f"🌍 Устанавливаем Webhook: {WEBHOOK_URL}/telegram")
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/telegram")
    print("✅ Telegram-бот запущен на Railway!")

async def on_cleanup(app):
    await application.stop()
    await application.shutdown()

app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    web.run_app(app, port=port)
else:
    # Используется в проде (Railway)
    async def main():
        await application.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 8000)),
            webhook_url=f"{WEBHOOK_URL}/telegram"
        )