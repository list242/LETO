import json
import os
import asyncio
import calendar
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
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
faq_data = {
    0: {
        "text": "📍 Наш маршрут проходит вдоль живописной набережной. Мы проезжаем ключевые достопримечательности и спокойные бухты.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    1: {
        "text": "📍 Мы находимся на [причале CBRental], по адресу: г. Москва, Набережная Х, причал Y. Припарковаться можно рядом.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    2: {
        "text": "🧍‍♂️ На каждой лодке удобно размещаются 4–5 человек. Для больших компаний — можно арендовать 2–3 лодки одновременно.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    3: {
        "text": "ℹ️ Ответ на этот вопрос будет добавлен позже.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    4: {
        "text": "ℹ️ Ответ на этот вопрос будет добавлен позже.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    5: {
        "text": "ℹ️ Ответ на этот вопрос будет добавлен позже.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    6: {
        "text": "ℹ️ Ответ на этот вопрос будет добавлен позже.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    7: {
        "text": "ℹ️ Ответ на этот вопрос будет добавлен позже.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    8: {
        "text": "ℹ️ Ответ на этот вопрос будет добавлен позже.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    9: {
        "text": "ℹ️ Ответ на этот вопрос будет добавлен позже.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    10: {
        "text": "ℹ️ Ответ на этот вопрос будет добавлен позже.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    11: {
        "text": "ℹ️ Ответ на этот вопрос будет добавлен позже.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    12: {
        "text": "💸 Цены указаны в разделе выбора лодки. Нажмите 'Выбор лодки' в главном меню, выберите лодку и ознакомьтесь с ценами перед бронированием.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    13: {
        "text": "ℹ️ Ответ на этот вопрос будет добавлен позже.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    14: {
        "text": "ℹ️ Ответ на этот вопрос будет добавлен позже.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    },
    15: {
        "text": "ℹ️ Ответ на этот вопрос будет добавлен позже.",
        "photo": "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"
    }
}


boat_photos = {
    "red": {
        "name": "🔴 Красная лодка",
        "photos": ["AgACAgIAAxkBAAILmmgvoQwSdGbRLV8B2eHeQDxMYe3VAALO7jEbVK2BSZBrnRn86OvnAQADAgADeQADNgQ",
                    "AgACAgIAAxkBAAIJ7mgiUEYejU9rCnWd8yx8ysmDNmQhAAL57jEbgsIQSWOL_YKwFvavAQADAgADeAADNgQ",
                   "AgACAgIAAxkBAAIJ6GgiUD5NLqLoj5Un3nugAdS0WfngAAL37jEbgsIQSbEtTl7AFoCcAQADAgADeAADNgQ",
                   "AgACAgIAAxkBAAIJ6mgiUEGWfGwdBJBIRqriTNeD-8vBAAL47jEbgsIQSWYCAAG1BP1zzgEAAwIAA3gAAzYE",
                   "AgACAgIAAxkBAAIJ7GgiUERUIu_cgof8ufLmRkowV1pGAALv7jEbnVAYSddk2aHgv3W0AQADAgADeAADNgQ",
                   "AgACAgIAAxkBAAILnGgvoRT5sR18zCgtDhdb0RuV6vSJAALP7jEbVK2BSdic7r0n4cilAQADAgADeQADNgQ",
                   "AgACAgIAAxkBAAILnmgvoRtcZaiKgWYHu8O3pxC_vHT4AALQ7jEbVK2BSTnsVBcO3cDtAQADAgADeQADNgQ",
                   "AgACAgIAAxkBAAILoGgvoSE2mFXzVFwr9NphFrLo88m9AAK67TEb-0-ASc1gliDJhp1IAQADAgADeQADNgQ"
                   ]
    },
    "blue": {
        "name": "🔵 Синяя лодка",
        "photos": ["AgACAgIAAxkBAAIJ8GgiUElXydOz_R9z48cvhP6BtT5eAAL67jEbgsIQSexV98cJYhdOAQADAgADeAADNgQ", 
                   "AgACAgIAAxkBAAILk2gvoLzKWTNJXGs9hyDZqkPJLKNVAALL7jEbVK2BSQ2qqjSgXpCfAQADAgADeQADNgQ",
                   "AgACAgIAAxkBAAILkWgvoLV6fd1aKMThNmO_57aPwbzIAALK7jEbVK2BSUhd53SS5TeiAQADAgADeQADNgQ",
                   "AgACAgIAAxkBAAIJ8mgiUE7NPZgAAVhr09ZZHdQZCU9j0QAC--4xG4LCEEmIYVaOPFt94QEAAwIAA3gAAzYE",
                   "AgACAgIAAxkBAAIJ9GgiUFFXrdawEuvENhkxpN9yhguxAAL87jEbgsIQSS9I60fWlkQiAQADAgADeAADNgQ"
                   ]
    },
    "white": {
        "name": "⚪ Белая лодка",
        "photos": ["AgACAgIAAxkBAAIJ_mgiUGcwDUaZrp-AFltDMoZrgmlgAAII7zEbgsIQSe7owVRTdxdvAQADAgADeAADNgQ",
                   "AgACAgIAAxkBAAILlWgvoO0E9rCaHFtn_jowf1mSYcxtAALM7jEbVK2BSaHDZQ9rUqnJAQADAgADeQADNgQ",
                   "AgACAgIAAxkBAAIJ_GgiUGM2eU9j3JhmLNcuXNDSDs8FAAIH7zEbgsIQSdPzhY6HtFF-AQADAgADeAADNgQ",
                   "AgACAgIAAxkBAAIJ-mgiUF62Nood_-nB2l_Bh_j3jfAUAAIG7zEbgsIQScILOejghOD4AQADAgADeAADNgQ",
                   "AgACAgIAAxkBAAILlWgvoO0E9rCaHFtn_jowf1mSYcxtAALM7jEbVK2BSaHDZQ9rUqnJAQADAgADeQADNgQ",
                   "AgACAgIAAxkBAAIJ9mgiUFlzMDnE-YU-WoWFe3SVlWmiAAIC7zEbgsIQSblwoFwi98XSAQADAgADeAADNgQ"
                   ]
    }
}

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
def get_weather_description(weather: dict) -> str:
    temp = weather.get("temp", "—")
    wind = weather.get("wind", "—")
    rain = weather.get("rain", False)
    print("🔥 handle_message вызван")
    if temp == "—":
        temp_desc = "Температура: неизвестна 🌡"
    elif temp < 10:
        temp_desc = f"Температура: {temp}°C — холодно, лучше надеть тёплую куртку 🧥"
    elif 10 <= temp < 18:
        temp_desc = f"Температура: {temp}°C — прохладно, пригодится лёгкая куртка 🌤"
    elif 18 <= temp < 25:
        temp_desc = f"Температура: {temp}°C — комфортно, отличная погода для прогулки 🚤"
    else:
        temp_desc = f"Температура: {temp}°C — жарко, не забудьте воду и головной убор ☀️"

    if wind == "—":
        wind_desc = "Ветер: неизвестен 🌬"
    elif wind < 3:
        wind_desc = f"Ветер: {wind} м/с — почти штиль, вода как зеркало 🪞"
    elif 3 <= wind < 6:
        wind_desc = f"Ветер: {wind} м/с — лёгкий ветерок, прогулка будет приятной 🛶"
    elif 6 <= wind < 10:
        wind_desc = f"Ветер: {wind} м/с — немного ветрено, стоит быть аккуратнее 🚩"
    else:
        wind_desc = f"Ветер: {wind} м/с — сильный ветер, лучше не выходить на воду 🌪"

    if rain:
        rain_desc = "Осадки: возможны — захвати дождевик, но не теряй оптимизм! 🌧"
    else:
        rain_desc = "Осадки: не ожидаются, день будет отличным ☀️"

    return f"{temp_desc}\n{wind_desc}\n{rain_desc}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[DEBUG] Callback received: {update.callback_query.data}")
    query = update.callback_query
    print("🔥 handle_message вызван")
    print("🔘 data =", update.callback_query.data)

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

            weather_text = f"📅 Вы выбрали дату: {selected_date}\n\n"
            weather_text += get_weather_description(weather)
            weather_text += "\n\nТеперь выберите время:"


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
        elif data == "faq":
            faq_items = [
                    "Какой маршрут",
                    "Где вы находитесь",
                    "Сколько человек помещается",
                    "Можно ли алкоголь",
                    "Хочу сделать предложение",
                    "Хочу подарить цветы",
                    "Я не умею управлять катером",
                    "Что делать в случае плохой погоды",
                    "Можно ли с детьми",
                    "Как отменить бронь",
                    "Как перенести бронь",
                    "Можно ли с домашними животными",
                    "Где увидеть цену",
                    "Можно ли сразу 2 или 3 катера",
                    "Можно ли арендовать для фотосессии",
                    "Сколько аренда по времени"
                ]
            keyboard = [[InlineKeyboardButton(q, callback_data=f"faq_{i}")] for i, q in enumerate(faq_items)]
            keyboard.append([InlineKeyboardButton("🏠 Назад в меню", callback_data="back_to_start")])
            await query.edit_message_text("📌 Выберите интересующий вопрос:", reply_markup=InlineKeyboardMarkup(keyboard))

        elif data.startswith("faq_"):
            idx = int(data.split("_")[1])
            faq = faq_data.get(idx)

            if faq:
                text = faq["text"]
                photo = faq["photo"]
                keyboard = [[InlineKeyboardButton("⬅️ Назад к вопросам", callback_data="faq")]]

                try:
                    await query.edit_message_media(
                        media=InputMediaPhoto(media=photo, caption=text),
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except Exception as e:
                    print("⚠️ Ошибка при показе FAQ с фото:", e)
                    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.edit_message_text("❓ Информация по этому вопросу пока не добавлена.")


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
            await query.answer()

            try:
                await query.message.delete()
            except Exception as e:
                print("⚠️ Не удалось удалить сообщение:", e)

            start_photo_file_id = "AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ"

            keyboard = [
                [InlineKeyboardButton("🚤 Выбор лодки", callback_data="select_boat")],
                [InlineKeyboardButton("📷 Фото лодок", callback_data="show_boat_photos")],
                [InlineKeyboardButton("📘 Пройти инструктаж", callback_data="start_quiz")],
                [InlineKeyboardButton("❓ Часто задаваемые вопросы", callback_data="faq")]
            ]

            await context.bot.send_photo(
                chat_id=query.from_user.id,
                photo=start_photo_file_id,
                caption="Добрый день, на связи cbrental🚩\nВыберите один из пунктов ниже, мы ответим на все ваши вопросы💫",
                reply_markup=InlineKeyboardMarkup(keyboard)
        )


        elif data.startswith("photo_"):
            parts = data.split("_")
            if len(parts) != 3:
                await query.answer("⚠️ Неверный формат callback_data")
                return

            _, boat, direction = parts
            index_key = f"photo_{boat}_index"

            photos = boat_photos[boat]["photos"]
            title = boat_photos[boat]["name"]
            current = context.user_data.get(index_key, 0)

            # Считаем новое значение current
            if direction == "start":
                current = 0
            elif direction == "next" and current + 1 < len(photos):
                current += 1
            elif direction == "prev" and current > 0:
                current -= 1
            else:
                await query.answer("Это крайнее фото.")
                return
            context.user_data[index_key] = current

            # ============ Формируем кнопки ============
            buttons = []

            # 1) Назад. Если это первая фотка — идём в выбор цвета лодки,
            # иначе — показываем предыдущую
            if current == 0:
                buttons.append(
                    InlineKeyboardButton(
                        "⬅️ Назад",
                        callback_data="boat_selection"   # вот он — ваш callback для возврата к цветам
                    )
                )
            else:
                buttons.append(
                    InlineKeyboardButton(
                        "⬅️ Назад",
                        callback_data=f"photo_{boat}_prev"
                    )
                )

            # 2) Вперёд — только если ещё есть куда листать
            if current + 1 < len(photos):
                buttons.append(
                    InlineKeyboardButton(
                        "➡️ Вперёд",
                        callback_data=f"photo_{boat}_next"
                    )
                )

            # Отправляем обновлённый медиа-месседж
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=photos[current],
                    caption=f"{title} ({current+1}/{len(photos)})"
                ),
                reply_markup=InlineKeyboardMarkup([buttons])
            )

        elif data == "show_boat_photos":
            await query.answer()
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media="AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ",
                    caption="📷 Фото лодок:\n\nВыберите лодку ниже"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔵 Синяя", callback_data="photo_blue_start")],
                    [InlineKeyboardButton("🔴 Красная", callback_data="photo_red_start")],
                    [InlineKeyboardButton("⚪ Белая", callback_data="photo_white_start")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
                ])
            )

        elif data == "boat_selection":
            keyboard = [
                [InlineKeyboardButton("🔵 Синяя", callback_data="photo_blue_start")],
                [InlineKeyboardButton("🔴 Красная", callback_data="photo_red_start")],
                [InlineKeyboardButton("⚪ Белая", callback_data="photo_white_start")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]

            await query.edit_message_media(
                media=InputMediaPhoto(
                    media="AgACAgIAAxkBAAILeGgvnC19UA1IsMjKaiV5O5dHGfy1AAKt7TEb-0-ASdJAcVd5KloXAQADAgADeQADNgQ",  # превью-фото
                    caption="📷 Фото лодок:\nВыберите цвет лодки ниже"
                ),
                reply_markup=InlineKeyboardMarkup(keyboard)
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
        
        # elif data == "help":
        #         keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
        #         reply_markup = InlineKeyboardMarkup(keyboard)
        #         await query.edit_message_text(
        #             "❓ Раздел помощи:\n"
        #             "1️⃣ Как забронировать лодку?\n"
        #             "2️⃣ Какие есть правила пользования лодкой?\n"
        #             "3️⃣ Как отменить бронь?\n"
        #             "🔙 Для возврата в меню нажмите кнопку ниже.",
        #             reply_markup=reply_markup
        #         )
        
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
from handlers.qa_search import search_answer
async def handle_text_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_question = update.message.text.strip()
    answer = search_answer(user_question)
    await update.message.reply_text(answer)
