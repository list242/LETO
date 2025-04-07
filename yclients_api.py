# yclients_api.py
import requests
from datetime import datetime, timedelta

YCLIENTS_USER_TOKEN = "eebe5959-8779-4670-a3a0-ab3a536f649d"
PARTNER_TOKEN = "tdp3ectpmhn5xkghbwns"
COMPANY_ID = 1275464
STAFF_ID = 3811393
SERVICE_ID = 19053129

def create_yclients_booking(name: str, phone: str, date: str, time: str) -> bool:
    datetime_start = f"{date}T{time}:00"
    start_dt = datetime.strptime(datetime_start, "%Y-%m-%dT%H:%M:%S")
    end_dt = start_dt + timedelta(minutes=90)

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
        "Partner-Token": PARTNER_TOKEN,
        "X-Partner-Id": "b7620716-df47-4fef-922b-99a18fe9e9f4",  # обязательный хак
        "Content-Type": "application/json",
        "Accept": "application/vnd.yclients.v2+json",
        "User-Agent": "bot_boats"
    }

    url = f"https://api.yclients.com/api/v1/records/{COMPANY_ID}"
    response = requests.post(url, json=payload, headers=headers)

    if response.ok:
        print("✅ YCLIENTS: запись создана", response.json())
        return True
    else:
        print("❌ YCLIENTS: ошибка", response.text)
        return False
