import requests
from datetime import datetime, timedelta

YCLIENTS_USER_TOKEN = "c4033acd6cf298f0c854a9e252ce6226"
PARTNER_TOKEN = "tdp3ectpmhn5xkghbwns"
PARTNER_ID = "8463"  # ← если вдруг он у тебя другой — поменяешь
COMPANY_ID = 1275464
STAFF_ID = 3813130
SERVICE_ID = 19053129

def create_yclients_booking(name: str, phone: str, date: str, time: str) -> dict:
    try:
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
            "X-Partner-Id": PARTNER_ID,
            "Content-Type": "application/json",
            "Accept": "application/vnd.yclients.v2+json",
            "User-Agent": "bot_boats"
        }

        # Логируем всё, что отправляем
        print("🔍 YCLIENTS: отправка запроса на создание брони")
        print("➡️ Заголовки:", headers)
        print("📦 Payload:", payload)

        url = f"https://api.yclients.com/api/v1/records/{COMPANY_ID}"
        response = requests.post(url, json=payload, headers=headers)

        print("📬 Ответ от YCLIENTS:", response.status_code, response.text)

        if response.ok:
            print("✅ Запись успешно создана:", response.json())
            return response.json()
        else:
            print("❌ Ошибка при создании записи:", response.text)

            # Дополнительный разбор, если ошибка связана с партнёрством
            if "Не указан идентификатор партнера" in response.text:
                print("⚠️ Похоже, X-Partner-Id некорректен или отсутствует.")
                print("💡 Убедитесь, что вы используете правильный partner_id, полученный при регистрации приложения.")
            
            return {"success": False, "error": response.text}

    except Exception as e:
        print("❌ Исключение при создании брони через YCLIENTS:", str(e))
        return {"success": False, "error": str(e)}
