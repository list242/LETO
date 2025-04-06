from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.get("/token")
async def capture_token(request: Request):
    user_token = request.query_params.get("user_token")
    if user_token:
        print(f"✅ Новый системный User Token: {user_token}")
        with open("yclients_token.txt", "w") as f:
            f.write(user_token)
    return {"status": "ok"}

@app.post("/disconnect")
async def disconnect_hook(request: Request):
    body = await request.body()
    print("🔌 Интеграция отключена. Payload:", body)
    return {"status": "received"}
