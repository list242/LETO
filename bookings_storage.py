# bookings_storage.py
import json
import os

BOOKINGS_FILE = "bookings.json"

def save_booking_to_file(user_id: int, booking_data: dict):
    """Сохраняет или обновляет бронь пользователя по user_id."""
    try:
        data = {}

        if os.path.exists(BOOKINGS_FILE):
            with open(BOOKINGS_FILE, "r", encoding="utf-8") as f:
                try:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                except json.JSONDecodeError:
                    print("⚠️ bookings.json повреждён или пуст — перезаписываем.")
                    data = {}

        data[str(user_id)] = booking_data

        with open(BOOKINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"✅ Бронь пользователя {user_id} сохранена.")
    except Exception as e:
        print(f"❌ Ошибка при сохранении брони: {e}")

def delete_booking(user_id: int):
    """Удаляет бронь пользователя по user_id."""
    try:
        if not os.path.exists(BOOKINGS_FILE):
            return

        with open(BOOKINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if str(user_id) in data:
            del data[str(user_id)]

            with open(BOOKINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            print(f"🗑️ Бронь пользователя {user_id} удалена.")
    except Exception as e:
        print(f"❌ Ошибка при удалении брони: {e}")

def get_booking(user_id: int) -> dict | None:
    """Возвращает бронь пользователя по user_id, если есть."""
    try:
        if not os.path.exists(BOOKINGS_FILE):
            return None

        with open(BOOKINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(str(user_id))
    except Exception as e:
        print(f"❌ Ошибка при получении брони: {e}")
        return None

def get_all_bookings() -> dict:
    """Возвращает все брони как словарь."""
    try:
        if os.path.exists(BOOKINGS_FILE):
            with open(BOOKINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"❌ Ошибка при чтении всех броней: {e}")
        return {}
