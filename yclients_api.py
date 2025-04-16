import requests
from datetime import datetime, timedelta
import os
import json

# === Конфигурация из переменных окружения ===
USER_TOKEN = os.getenv("USER_TOKEN", "9641e267767c2135bdb487c686569a0c")
PARTNER_TOKEN = os.getenv("PARTNER_TOKEN", "4a4jpwj3su8kecfw46t9")
X_PARTNER_ID = os.getenv("X_PARTNER_ID", "8572")

COMPANY_ID = int(os.getenv("COMPANY_ID", "1283794"))
DEFAULT_STAFF_ID = int(os.getenv("DEFAULT_STAFF_ID", "3832174"))

# Услуги по цвету лодки
SERVICE_IDS = {
    "Синяя": 19177553,
    "Белая": 19177559,
    "Красная": 19177302
}

def create_yclients_booking(name: str, phone: str, date: str, time: str, boat: str, staff_id: int = DEFAULT_STAFF_ID) -> dict:
    """
    Создаёт запись в YCLIENTS для выбранной лодки, даты и времени.
    """
    datetime_start = f"{date}T{time}:00"
    start_dt = datetime.strptime(datetime_start, "%Y-%m-%dT%H:%M:%S")
    end_dt = start_dt + timedelta(minutes=90)

    service_id = SERVICE_IDS.get(boat)
    if not service_id:
        print(f"❌ Неизвестная лодка: {boat}")
        return {"success": False, "error": f"Неизвестная лодка: {boat}"}

    payload = {
        "staff_id": staff_id,
        "services": [{"id": service_id}],
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

    print("=" * 60)
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
            print("⚠️ Ошибка 401 Unauthorized. Проверьте токены и X-Partner-Id.")
        elif response.status_code == 403:
            print("🚫 Доступ запрещён. У пользователя нет прав.")
        elif response.status_code == 422:
            print("📛 Неверный формат данных. Проверь payload.")
        elif response.status_code >= 500:
            print("🔥 Ошибка сервера YCLIENTS.")
        else:
            print("❌ Неизвестная ошибка:", response.status_code, response.text)

    except Exception as e:
        print(f"💥 Исключение при отправке запроса: {e}")

    return {"success": False, "error": "Не удалось создать запись"}

def get_yclients_bookings(date: str) -> list:
    """
    Получает список всех записей на выбранную дату.
    """
    headers = {
        "Authorization": f"Bearer {PARTNER_TOKEN}, User {USER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.yclients.v2+json",
        "X-Partner-Id": X_PARTNER_ID
    }

    url = f"https://api.yclients.com/api/v1/records/{COMPANY_ID}?date={date}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            print("⚠️ Не удалось получить записи:", response.status_code, response.text)
    except Exception as e:
        print("💥 Ошибка при запросе записей:", e)

    return []
