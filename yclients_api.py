
import requests
from datetime import datetime, timedelta
import os

# === Конфигурация (можно задавать через переменные среды) ===
STAFF_LOGIN = os.getenv("STAFF_LOGIN", "79852482448")
STAFF_PASSWORD = os.getenv("STAFF_PASSWORD", "MatveyKrutoi228")
COMPANY_ID = int(os.getenv("COMPANY_ID", "1275464"))
DEFAULT_STAFF_ID = int(os.getenv("DEFAULT_STAFF_ID", "3813130"))
SERVICE_ID = int(os.getenv("SERVICE_ID", "19053129"))
def get_user_token(login: str, password: str) -> str:
    url = "https://api.yclients.com/api/v1/auth"
    payload = {
        "login": "79852482448",
        "password": "MatveyKrutoi228",
    }


    headers = {
        "Content-Type": "application/json"
    }
    print("🔍 Логин:", login)
    print("🔍 Пароль:", "*" * len(password))

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("🔐 Запрос на получение user_token:", response.status_code, response.text)

        if response.status_code == 200 and response.json().get("success"):
            token = response.json()["data"]["user_token"]
            print("✅ Получен user_token:", token)
            return token
        else:
            print("❌ Не удалось получить user_token:", response.text)
            return None
    except Exception as e:
        print("❌ Ошибка при получении user_token:", str(e))
        return None

def create_yclients_booking(name: str, phone: str, date: str, time: str, staff_id: int = DEFAULT_STAFF_ID) -> dict:
    user_token = get_user_token(STAFF_LOGIN, STAFF_PASSWORD)
    if not user_token:
        return {"success": False, "error": "Не удалось получить user_token"}

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
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.yclients.v2+json",
        "User-Agent": "bot_boats"
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
