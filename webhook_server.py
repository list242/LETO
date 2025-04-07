from fastapi import FastAPI, Request
from bot import application
import telegram

app = FastAPI()

@app.on_event("startup")
async def setup_webhook():
    await application.initialize()  # важно!
    await application.start()       # важно!
    await application.bot.set_webhook("https://leto-production.up.railway.app/webhook")
    print("🚀 Webhook установлен")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = telegram.Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}
