# webhook_server.py
from fastapi import FastAPI, Request
from bot import application
import telegram

app = FastAPI()

import os

@app.on_event("startup")
async def setup_webhook():
    webhook_url = "https://leto-production.up.railway.app/webhook"
    await application.bot.set_webhook(webhook_url)
    print(f"🚀 Webhook установлен: {webhook_url}")


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = telegram.Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}
