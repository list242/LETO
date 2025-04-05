import requests
from datetime import datetime, timedelta

YCLIENTS_USER_TOKEN = "c4033acd6cf298f0c854a9e252ce6226"
COMPANY_ID = 1275464
STAFF_ID = 3811393
SERVICE_ID = 19053129

def create_yclients_booking(name: str, phone: str, date: str, time: str) -> dict:

    datetime_start = f"{date}T{time}:00"
    start_dt = datetime.strptime(datetime_start, "%Y-%m-%dT%H:%M:%S")
    end_dt = start_dt + timedelta(minutes=90)  # Бронь на 1.5 часа

    payload = {
        "staff_id": STAFF_ID,
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
        "Authorization": f"Bearer {YCLIENTS_USER_TOKEN}",
        "Content-Type": "application/json"
    }

    url = f"https://api.yclients.com/api/v1/records/{COMPANY_ID}"
    response = requests.post(url, json=payload, headers=headers)

    if response.ok:
        print("✅ Запись успешно создана")
    else:
        print("❌ Ошибка при создании записи:", response.text)

    return response.json()
