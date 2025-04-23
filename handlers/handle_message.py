import json
import os
import asyncio
import calendar
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.utils import (
    generate_date_keyboard,
    notify_admin,
    ENTERING_PHONE,
    ENTERING_NAME,
    enter_name,
    enter_phone,
    get_taken_slots,
    is_slot_taken_yclients,
    load_admins,
)

from bookings_storage import (
    save_booking_to_file,
    delete_booking,
    get_booking,
    get_all_bookings,
)

from weather import get_weather_for_date
from yclients_api import (
    create_yclients_booking,
    get_yclients_bookings,
    DEFAULT_STAFF_ID,
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query:
        user_chat_id = update.effective_user.id
        admins = load_admins()
        if user_chat_id not in admins and any([
            context.bot_data.get(f"pending-{user_chat_id}"),
            context.bot_data.get(f"reschedule-{user_chat_id}"),
            context.bot_data.get(f"cancel-{user_chat_id}")
        ]):
            await query.answer("⏳ Ожидайте подтверждения от администратора.")
            return

        await query.answer() 
        data = query.data

        if data in ["blue", "red", "white"]:
            selected_boat = {
                "blue": "Синяя",
                "red": "Красная",
                "white": "Белая"
            }[data]
            context.user_data["selected_boat"] = selected_boat

            today = datetime.now().date()
            context.user_data["current_week_start"] = today

            keyboard = generate_date_keyboard(today, context)
            reply_markup = keyboard

            await query.edit_message_text(
                f"Вы выбрали лодку {selected_boat}. Теперь выберите дату:",
                reply_markup=reply_markup
            )

        elif data.startswith("date-"):
            selected_date = data.replace("date-", "", 1)
            try:
                datetime.fromisoformat(selected_date)
                context.user_data["selected_date"] = selected_date
            except ValueError:
                await query.edit_message_text("Некорректный формат даты. Пожалуйста, попробуйте снова.")
                return

            # Получаем прогноз погоды для выбранной даты
            weather = get_weather_for_date(selected_date)

            weather_text = (
                f"📅 Вы выбрали {selected_date}\n"
                f"🌡️ Температура: {weather['temp']}°C\n"
                f"💨 Ветер: {weather['wind']} м/с\n"
            )
            if weather["rain"]:
                weather_text += "🌧️ Осадки: возможны\n"

            weather_text += "\nТеперь выберите время:"

            time_slots = [
                "11:00 - 12:30",
                "13:00 - 14:30",
                "15:00 - 16:30",
                "17:00 - 18:30",
                "19:00 - 20:30",
                "21:00 - 22:30"
            ]
            staff_map = {
                "Синяя": 3832174,
                "Красная": 3832174,
                "Белая": 3832174
            }

            boat = context.user_data.get("selected_boat")
            staff_id = staff_map.get(boat, DEFAULT_STAFF_ID)
            taken_slots = get_taken_slots(selected_date, boat, staff_id)

            available_slots = [
                [InlineKeyboardButton(slot, callback_data=f"time-{slot}")]
                for slot in time_slots if slot not in taken_slots
            ]

            if not available_slots:
                available_slots.append([InlineKeyboardButton("❌ Все слоты заняты", callback_data="back")])

            available_slots.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
            reply_markup = InlineKeyboardMarkup(available_slots)

            await query.edit_message_text(
                text=weather_text,
                reply_markup=reply_markup
            )


        elif data == "go_back":

            keyboard = [
                [InlineKeyboardButton("Синяя лодка", callback_data="blue")],
                [InlineKeyboardButton("Красная лодка", callback_data="red")],
                [InlineKeyboardButton("Белая лодка", callback_data="white")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Выберите лодку:", reply_markup=reply_markup)


            context.user_data.pop("user_name", None)
            context.user_data.pop("phone_number", None)
            context.user_data["state"] = None

        elif data == "back":

            current_week_start = context.user_data.get("current_week_start", datetime.now().date())
            prev_week_start = current_week_start - timedelta(days=7)
            if prev_week_start < datetime.now().date():
                keyboard = [
                        [InlineKeyboardButton("Синяя лодка", callback_data="blue")],
                        [InlineKeyboardButton("Красная лодка", callback_data="red")],
                        [InlineKeyboardButton("Белая лодка", callback_data="white")],
                        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
                    ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "Здравствуйте! Какую лодку хотите выбрать?",
                    reply_markup=reply_markup
                )
            else:

                context.user_data["current_week_start"] = prev_week_start
                keyboard = generate_date_keyboard(prev_week_start, context)
                reply_markup = keyboard
                boat = context.user_data.get("selected_boat")
                await query.edit_message_text(
                    f"Вы выбрали лодку {boat}. Теперь выберите дату:",
                    reply_markup=reply_markup
                )
        elif data == "back_to_start":
            if context.bot_data.get(f"pending-{user_chat_id}"):
                await query.answer("⏳ Ожидайте подтверждения от администратора.")
                return
            keyboard = []
            if get_booking(user_chat_id):

                keyboard.append([InlineKeyboardButton("📌 Моя запись", callback_data="my_booking")])

            else:
                keyboard.append([InlineKeyboardButton("🚤 Выбор лодки", callback_data="select_boat")])

            keyboard.append([InlineKeyboardButton("📘 Пройти инструктаж", callback_data="start_quiz")])
            keyboard.append([InlineKeyboardButton("ℹ️ Помощь", callback_data="help")])
            keyboard.append([InlineKeyboardButton("❓ Частые вопросы", callback_data="faq")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "👋 Добро пожаловать! Выберите один из пунктов ниже:", 
                reply_markup=reply_markup
            )



        elif data == "forward":
            current_week_start = context.user_data.get("current_week_start", datetime.now().date())
            next_week_start = current_week_start + timedelta(days=7)
            context.user_data["current_week_start"] = next_week_start 


            keyboard = generate_date_keyboard(next_week_start, context)
            reply_markup = keyboard

            boat = context.user_data.get("selected_boat")
            await query.edit_message_text(
                f"Вы выбрали лодку {boat}. Теперь выберите дату:",
                reply_markup=reply_markup
            )
        elif data == "faq":
                keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "📌 Частые вопросы:\n"
                    "- 📅 Можно ли перенести бронь?\n"
                    "- ⚓ Какие условия аренды?\n"
                    "- 👶 Есть ли ограничения по возрасту?\n"
                    "🔙 Для возврата в меню нажмите кнопку ниже.",
                    reply_markup=reply_markup
                )
        elif data == "my_booking":
            booking = get_booking(user_chat_id)
            if not booking:
                await query.edit_message_text("❌ У вас нет активной записи.")
                return
            boat = context.user_data.get("selected_boat", "🚤 Не выбрано")
            date = context.user_data.get("selected_date", "📅 Не выбрано")
            time = context.user_data.get("selected_time", "⏰ Не выбрано")
            name = context.user_data.get("user_name", "❓ Не указано")
            phone = context.user_data.get("phone_number", "❓ Не указано")

            message = (
                f"📌 Ваша запись:\n"
                f"- Лодка: {boat}\n"
                f"- Дата: {date}\n"
                f"- Время: {time}\n"
                f"- Имя: {name}\n"
                f"- Телефон: {phone}"
            )
            keyboard = [
                [InlineKeyboardButton("🏠 Выйти в меню", callback_data="back_to_start")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(message, reply_markup=reply_markup)

        # Перенос бронирования

        elif data == "help":
                keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❓ Раздел помощи:\n"
                    "1️⃣ Как забронировать лодку?\n"
                    "2️⃣ Какие есть правила пользования лодкой?\n"
                    "3️⃣ Как отменить бронь?\n"
                    "🔙 Для возврата в меню нажмите кнопку ниже.",
                    reply_markup=reply_markup
                )
        
        elif data.startswith("time-"):
            if get_booking(user_chat_id):
                await query.answer("❗ У вас уже есть активная запись.")
                return

            selected_time = data.replace("time-", "", 1)
            context.user_data["selected_time"] = selected_time
            context.user_data["state"] = ENTERING_NAME

            boat = context.user_data.get("selected_boat")
            date = context.user_data.get("selected_date")

            if not date or not isinstance(date, str):
                await query.edit_message_text("Ошибка при выборе даты. Попробуйте снова.")
                return

            try:
                formatted_date = datetime.fromisoformat(date).strftime('%d.%m.%Y')
            except ValueError:
                await query.edit_message_text("Некорректный формат даты. Попробуйте снова.")
                return

            text = (
                f"📌 Вы выбрали:\n"
                f"- Лодка: {boat}\n"
                f"- Дата: {formatted_date}\n"
                f"- Время: {selected_time}\n\n"
                f"✍️ Введите ваше имя:"
            )

            await query.edit_message_text(text=text)

            context.user_data["booking_message_id"] = query.message.message_id

            return ENTERING_NAME
