from datetime import datetime, timedelta  # ✅ Добавили datetime и timedelta
import calendar  # ✅ Добавили calendar
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from handlers.button_handler import ContextTypes, ConversationHandler  # ✅ Добавили ContextTypes и ConversationHandler
from datetime import datetime
import json
import requests
import os
from yclients_api import get_yclients_bookings
ADMIN_FILE = "admins.json"
MAX_DATE = datetime(2025, 8, 31).date()
ENTERING_NAME, ENTERING_PHONE = range(2)
RUSSIAN_DAY_ABBREVIATIONS = {0: "Пн",1: "Вт",2: "Ср",3: "Чт",4: "Пт",5: "Сб",6: "Вс"}

def is_slot_taken_yclients(date: str, time_range: str, staff_id: int) -> bool:
    bookings = get_yclients_bookings(date)
    start_time = time_range.split(" - ")[0]

    for b in bookings:
        b_time = b.get("datetime", "")
        b_staff_id = b.get("staff", {}).get("id")

        if b_staff_id == staff_id and b_time.endswith(f"{start_time}:00"):
            return True
    return False


def load_admins():
    try:
        with open(ADMIN_FILE, "r", encoding="utf-8") as file:
            return set(json.load(file))  # Загружаем список администраторов
    except FileNotFoundError:
        return set()  # Если файл не найден, возвращаем пустое множество

def format_date(date):
    day_name = RUSSIAN_DAY_ABBREVIATIONS[date.weekday()]  
    return f"{date.strftime('%d.%m.%Y')} ({day_name})"

def load_admins():
    """Загружает список админов из JSON-файла."""
    admins_file = os.path.join(os.path.dirname(__file__), "..", "admins.json")
    try:
        with open(admins_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    
def generate_date_keyboard(start_date, context):
    keyboard = []
    current_date = start_date + timedelta(days=1) 
    days_shown = 0

    if start_date == datetime.now().date():
        while days_shown < 7 and current_date.weekday() != calendar.SUNDAY and current_date <= MAX_DATE:
            date_str = format_date(current_date)  
            callback_data = f"date-{current_date.isoformat()}"  
            keyboard.append([InlineKeyboardButton(date_str, callback_data=callback_data)])
            current_date += timedelta(days=1)
            days_shown += 1

        if current_date.weekday() == calendar.SUNDAY and current_date <= MAX_DATE:
            date_str = format_date(current_date) 
            callback_data = f"date-{current_date.isoformat()}"  
            keyboard.append([InlineKeyboardButton(date_str, callback_data=callback_data)])

    else:
        if current_date.weekday() != 0:
            days_until_monday = (7 - current_date.weekday()) % 7
            current_date += timedelta(days=days_until_monday)

        for _ in range(7):
            if current_date > MAX_DATE:
                break 
            date_str = format_date(current_date)  
            callback_data = f"date-{current_date.isoformat()}" 
            keyboard.append([InlineKeyboardButton(date_str, callback_data=callback_data)])
            current_date += timedelta(days=1)

    if current_date > MAX_DATE:
        keyboard.append([InlineKeyboardButton("Назад", callback_data="back")])
    else:
        keyboard.append([InlineKeyboardButton("Назад", callback_data="back")])
        keyboard.append([InlineKeyboardButton("Вперед", callback_data="forward")])
    return InlineKeyboardMarkup(keyboard)

async def notify_admin(context: ContextTypes.DEFAULT_TYPE, message: str, user_chat_id: int):
    admin_chat_ids = load_admins()  # Загружаем администраторов
    if not admin_chat_ids:
        print("Нет администраторов для уведомления.")
        return

    for admin_chat_id in admin_chat_ids:
        try:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Одобрить", callback_data=f"approve-{user_chat_id}"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"reject-{user_chat_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(chat_id=admin_chat_id, text=message, reply_markup=reply_markup)
            print(f"✅ Уведомление отправлено администратору {admin_chat_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки администратору {admin_chat_id}: {e}")

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    
    if not user_input or len(user_input) < 2:
        await update.message.reply_text("Имя должно содержать минимум 2 символа. Попробуйте снова:")
        return ENTERING_NAME

    context.user_data["user_name"] = user_input
    context.user_data["state"] = ENTERING_PHONE  # Явно устанавливаем состояние

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Введите ваш номер телефона:", reply_markup=reply_markup)
    return ENTERING_PHONE

import re

async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    user_chat_id = update.effective_user.id
    context.bot_data[f"pending-{user_chat_id}"] = True
    context.bot_data[f"pending_msg_id-{user_chat_id}"] = update.message.message_id

    # Проверяем формат номера телефона
    phone_pattern = re.compile(r"^\+?\d{10,15}$")  # Допускаем + в начале, 10-15 цифр
    if not phone_pattern.match(user_input):
        await update.message.reply_text(
            "Некорректный номер телефона. Введите в формате +79037799664, 89037799664 или 79037799664:"
        )
        return ConversationHandler.END  # Или ENTERING_PHONE, если хочешь оставить в этом состоянии

    # Приводим номер к формату +7XXXXXXXXXX
    if user_input.startswith("8"):
        user_input = "+7" + user_input[1:]
    elif not user_input.startswith("+7"):
        user_input = "+7" + user_input

    # Сохраняем номер в user_data
    context.user_data["phone_number"] = user_input
    context.user_data.pop("state", None)

    # Получаем остальные данные пользователя
    boat = context.user_data.get("selected_boat", "Не выбрано")
    date = context.user_data.get("selected_date", "Не выбрано")
    time = context.user_data.get("selected_time", "Не выбрано")
    name = context.user_data.get("user_name", "Не указано")
    phone = context.user_data.get("phone_number", "Не указано")

    # Формируем сообщение для администратора
    admin_message = (
        f"🔔 **Новая заявка на бронирование!**\n"
        f"- 🚤 Лодка: {boat}\n"
        f"- 📅 Дата: {date}\n"
        f"- ⏰ Время: {time}\n"
        f"- 👤 Имя: {name}\n"
        f"- 📞 Телефон: {phone}"
    )

    # Формируем сообщение подтверждения для пользователя
    confirmation_message = (
        f"📌 Ваша запись:\n"
        f"- Лодка: {boat}\n"
        f"- Дата: {date}\n"
        f"- Время: {time}\n"
        f"- Имя: {name}\n"
        f"- Телефон: {phone}\n"
        f"✅ Ваша заявка отправлена администратору. Ожидайте подтверждения."
    )

    # Кнопки для пользователя
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="go_back")],
        [InlineKeyboardButton("🏠 Выйти в меню", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем подтверждение пользователю
    sent = await update.message.reply_text(confirmation_message, reply_markup=reply_markup)
    context.user_data["booking_message_id"] = sent.message_id

    # Уведомляем администратора
    user_chat_id = update.effective_user.id
    user_chat_id = update.effective_user.id

    context.bot_data[user_chat_id] = {
        "selected_boat": boat,
        "selected_date": date,
        "selected_time": time,
        "user_name": name,
        "phone_number": phone
    }
    await notify_admin(context, admin_message, user_chat_id)

    return ConversationHandler.END
BOOKINGS_FILE = "bookings.json"

def save_booking_to_file(user_id, booking_data):
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


def delete_booking(user_id):
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
def create_yclients_booking(data: dict):
    url = "https://api.yclients.com/api/v1/record"
    headers = {
        "Authorization": "Bearer c4033acd6cf298f0c854a9e252ce6226",
        "Content-Type": "application/json"
    }

    payload = {
        "company_id": 1275464,
        "service_ids": [19053129],  # Прокат лодки
        "staff_id": 3811393,        # Сотрудник
        "datetime": f"{data['selected_date']}T{data['start_time']}:00",
        "client": {
            "name": data["user_name"],
            "phone": data["phone_number"]
        },
        "comment": f"Лодка: {data['selected_boat']}, Время: {data['selected_time']}"
    }

    response = requests.post(url, json=payload, headers=headers)
    print("➡️ Отправка брони в YCLIENTS:", response.status_code, response.text)

    return response.status_code == 200