# yclients_api.py
import requests
from datetime import datetime, timedelta

YCLIENTS_USER_TOKEN = "c4033acd6cf298f0c854a9e252ce6226"
PARTNER_TOKEN = "tdp3ectpmhn5xkghbwns"
COMPANY_ID = 1275464
STAFF_IDS = {
    "Алексей": 3811393,
    "Матвей": 3813130
}
SERVICE_ID = 19053129

def create_yclients_booking(name: str, phone: str, date: str, time: str, staff_name="Алексей") -> bool:
    datetime_start = f"{date}T{time}:00"
    start_dt = datetime.strptime(datetime_start, "%Y-%m-%dT%H:%M:%S")
    seance_length = 90 * 60  # 90 минут в секундах

    payload = {
        "staff_id": STAFF_IDS.get(staff_name, STAFF_IDS["Алексей"]),
        "services": [{"id": SERVICE_ID}],
        "datetime": datetime_start,
        "seance_length": seance_length,
        "client": {
            "name": name,
            "phone": phone
        },
        "send_sms": True
    }

    headers = {
        "Authorization": f"Bearer {YCLIENTS_USER_TOKEN}",
        "Partner-Token": PARTNER_TOKEN,
        "X-Partner-Id": "8463",
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
