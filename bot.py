import os
import json
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, MessageHandler,
    ContextTypes, filters
)

from handlers.button_handler import (
    start_handler, callback_handler, boat_handler,
    register_admin, start_quiz, handle_quiz_answer
)
from handlers.handle_message import handle_text_question
from bookings_storage import delete_booking
from handlers.utils import load_admins

# ───────────────────────────────
# Инициализация бота и FastAPI
# ───────────────────────────────
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден")

application = Application.builder().token(TOKEN).build()
app = FastAPI()

# ───────────────────────────────
# Webhook endpoint
# ───────────────────────────────
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"status": "ok"}

# ───────────────────────────────
# Обработчик одобрения/отклонения заявки
# ───────────────────────────────
async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, user_id_str = query.data.split("-")
    user_id = int(user_id_str)
    admins = load_admins()

    if update.effective_user.id not in admins:
        await query.edit_message_text("❌ У вас нет прав для этого действия.")
        return

    if action == "approve":
        await context.bot.send_message(chat_id=user_id, text="✅ Ваша бронь подтверждена администратором.")
        await query.edit_message_text("✅ Заявка одобрена.")
    elif action == "reject":
        await context.bot.send_message(chat_id=user_id, text="❌ Ваша бронь отклонена администратором.")
        await query.edit_message_text("❌ Заявка отклонена.")
        delete_booking(user_id)

    context.bot_data.pop(f"pending-{user_id}", None)
    context.bot_data.pop(f"booking_msg_id-{user_id}", None)

# ───────────────────────────────
# Получение file_id фото
# ───────────────────────────────
async def get_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo = update.message.photo[-1]
        await update.message.reply_text(f"📎 File ID: {photo.file_id}")

# ───────────────────────────────
# Регистрация обработчиков
# ───────────────────────────────
application.add_handler(CallbackQueryHandler(handle_approval, pattern=r"^(approve|reject)-\d+$"))
application.add_handler(MessageHandler(filters.PHOTO, get_file_id))
application.add_handler(start_handler)
application.add_handler(boat_handler)
application.add_handler(CommandHandler("register", register_admin))
application.add_handler(CommandHandler("start_quiz", start_quiz))
application.add_handler(CallbackQueryHandler(start_quiz, pattern="^start_quiz$"))
application.add_handler(CallbackQueryHandler(handle_quiz_answer, pattern=r"^quiz_\d+_\d+$"))
application.add_handler(callback_handler)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_question))

# ───────────────────────────────
# Установка Webhook и запуск
# ───────────────────────────────
if __name__ == "__main__":
    import asyncio

    async def main():
        # Установка webhook
        webhook_url = "https://leto-pxzn.onrender.com/webhook"
        await application.bot.set_webhook(webhook_url)

        await application.initialize()
        await application.start()
        print("✅ Бот запущен через Webhook на Render.")

    asyncio.run(main())
