
import requests
from datetime import datetime, timedelta
import os
import json

# === Конфигурация (можно задавать через переменные среды) ===
USER_TOKEN = os.getenv("USER_TOKEN", "c4033acd6cf298f0c854a9e252ce6226")

PARTNER_IDS_TO_TRY = [
    os.getenv("X_PARTNER_ID"),
    "8463",
    "18400",
    "1275464",
    os.getenv("COMPANY_ID"),
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

    # Проверяем токен на очевидные ошибки
    if not USER_TOKEN or len(USER_TOKEN) < 10:
        print("❌ USER_TOKEN отсутствует или подозрительно короткий.")
        return {"success": False, "error": "Недопустимый user_token"}

    for partner_id in PARTNER_IDS_TO_TRY:
        if not partner_id:
            continue

        headers = {
            "Authorization": f"Bearer {USER_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.yclients.v2+json",
            "User-Agent": "bot_boats",
            "X-Partner-Id": str(partner_id)
        }

        print("="*50)
        print(f"🔁 Пробуем X-Partner-Id = {partner_id}")
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
                if "партнер" in response.text.lower():
                    print("🧩 Подсказка: возможно, X-Partner-Id неверный или не привязан к user_token.")
                elif "token" in response.text.lower():
                    print("🔐 Подсказка: возможно, user_token устарел или не принадлежит этому приложению.")
                else:
                    print("🧠 Прочее: возможная причина ошибки — несовпадение токена и партнёрского ID.")

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

    print("❌ Все X-Partner-Id проверены — неудача.")
    return {"success": False, "error": "X-Partner-Id validation failed"}
