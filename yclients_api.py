import requests
from datetime import datetime

API_BASE = "https://api.yclients.com/api/v1"

CLIENT_ID = "18400"
USER_TOKEN = "c4033acd6cf298f0c854a9e252ce6226"

COMPANY_ID = 1275464
STAFF_ID = 3811393
SERVICE_ID = 19053129

headers = {
    "Authorization": f"Bearer {USER_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def create_booking(name, phone, dt: datetime, comment="Бронь через Telegram"):
    payload = {
        "staff_id": STAFF_ID,
        "services": [{"id": SERVICE_ID}],
        "client": {
            "name": name,
            "phone": phone
        },
        "datetime": dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "comment": comment
    }

    response = requests.post(
        f"{API_BASE}/records/{COMPANY_ID}",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        print("✅ Бронь создана в Yclients:", response.json())
        return response.json()
    else:
        print("❌ Ошибка при бронировании:", response.status_code, response.text)
        return None

# Использование в Telegram-боте:
# from yclients_api import create_booking
# dt = datetime.fromisoformat("2025-04-10T15:00:00")
# create_booking("Иван", "+79035551234", dt)
