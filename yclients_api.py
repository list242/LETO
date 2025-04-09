
import requests
from datetime import datetime, timedelta
import os

# === Конфигурация (можно задавать через переменные среды) ===
USER_TOKEN = os.getenv("USER_TOKEN", "c4033acd6cf298f0c854a9e252ce6226")
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

    headers = {
        "Authorization": f"Bearer {USER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.yclients.v2+json",
        "User-Agent": "bot_boats",
        "X-Partner-Id": "1275464"
    }


    print("➡️ Заголовки:", headers)
    print("📦 Payload:", payload)

    url = f"https://api.yclients.com/api/v1/records/{COMPANY_ID}"
    response = requests.post(url, json=payload, headers=headers)

    print("📬 Ответ от YCLIENTS:", response.status_code, response.text)

    if response.status_code == 200:
        print("✅ Запись успешно создана:", response.json())
        return response.json()
    else:
        return {"success": False, "error": response.text}
