
import requests
from datetime import datetime, timedelta
import os

# === Конфигурация (можно задавать через переменные среды) ===
YCLIENTS_USER_TOKEN = os.getenv("YCLIENTS_USER_TOKEN", "c4033acd6cf298f0c854a9e252ce6226")
PARTNER_TOKEN = os.getenv("PARTNER_TOKEN", "tdp3ectpmhn5xkghbwns")
PARTNER_IDS_TO_TRY = [
    os.getenv("X_PARTNER_ID"),  # в .env или Railway Secrets
    "8463",  # старый из примера
    "18400",  # Application ID
    "1275464",  # ID филиала
]
COMPANY_ID = int(os.getenv("COMPANY_ID", "1275464"))
DEFAULT_STAFF_ID = int(os.getenv("DEFAULT_STAFF_ID", "3813130"))
SERVICE_ID = int(os.getenv("SERVICE_ID", "19053129"))

def create_yclients_booking(name: str, phone: str, date: str, time: str, staff_id: int = DEFAULT_STAFF_ID) -> dict:
    datetime_start = f"{date}T{time}:00"
    start_dt = datetime.strptime(datetime_start, "%Y-%m-%dT%H:%M:%S")
    end_dt = start_dt + timedelta(minutes=90)

    payload = {
        "staff_id": staff_id,
        "services": [{"id": SERVICE_ID}],
        "datetime": datetime_start,
        "seance_length": 90 * 60,
        "client": {
            "name": name,
            "phone": phone
        },
        "send_sms": True
    }

    # Попробуем все варианты X-Partner-Id
    for partner_id in PARTNER_IDS_TO_TRY:
        if not partner_id:
            continue

        headers = {
            "Authorization": f"Bearer {YCLIENTS_USER_TOKEN}",
            "Partner-Token": PARTNER_TOKEN,
            "X-Partner-Id": partner_id,
            "Content-Type": "application/json",
            "Accept": "application/vnd.yclients.v2+json",
            "User-Agent": "bot_boats"
        }

        print(f"🔁 Попытка с X-Partner-Id = {partner_id}")
        print("➡️ Заголовки:", headers)
        print("📦 Payload:", payload)

        url = f"https://api.yclients.com/api/v1/records/{COMPANY_ID}"
        response = requests.post(url, json=payload, headers=headers)

        print("📬 Ответ от YCLIENTS:", response.status_code, response.text)

        if response.status_code == 200:
            print("✅ Запись успешно создана:", response.json())
            return response.json()

        if response.status_code == 401:
            print("⚠️ Ошибка 401: Unauthorized — возможно, неверный X-Partner-Id.")
            continue  # пробуем следующий ID

    print("❌ Все попытки завершились неудачей.")
    return {"success": False, "error": "All partner ID attempts failed"}
