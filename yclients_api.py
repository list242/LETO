
import requests
from datetime import datetime, timedelta
import os
import json

# === Конфигурация ===
USER_TOKEN = os.getenv("USER_TOKEN", "c4033acd6cf298f0c854a9e252ce6226")
PARTNER_TOKEN = os.getenv("PARTNER_TOKEN", "tdp3ectpmhn5xkghbwns")
X_PARTNER_ID = os.getenv("X_PARTNER_ID", "8463")

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
        "Authorization": f"Bearer {PARTNER_TOKEN}, User {USER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.yclients.v2+json",
        "User-Agent": "bot_boats",
        "X-Partner-Id": X_PARTNER_ID
    }

    print("="*50)
    print("➡️ Заголовки:", json.dumps(headers, ensure_ascii=False, indent=2))
    print("📦 Payload:", json.dumps(payload, ensure_ascii=False, indent=2))

    url = f"https://api.yclients.com/api/v1/records/{COMPANY_ID}"
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("📬 HTTP:", response.status_code)
        print("📨 Ответ от YCLIENTS:", response.text)

        if response.status_code == 200:
            print("✅ Запись успешно создана")
            return response.json()
        elif response.status_code == 401:
            print("⚠️ Ошибка 401 Unauthorized.")
            print("🧩 Проверьте соответствие user_token + partner_token + X-Partner-Id.")
        elif response.status_code == 403:
            print("🚫 Доступ запрещён. Возможно, не хватает прав у системного пользователя.")
        elif response.status_code == 422:
            print("📛 Ошибка 422: Неверный формат данных. Проверьте payload.")
        elif response.status_code >= 500:
            print("🔥 Ошибка сервера YCLIENTS. Подождите и попробуйте позже.")
        else:
            print("❌ Неизвестная ошибка:", response.status_code, response.text)

    except Exception as e:
        print(f"💥 Исключение при запросе: {e}")

    return {"success": False, "error": "Не удалось создать запись"}
