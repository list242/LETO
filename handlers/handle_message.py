import json
import os
import asyncio
import calendar
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.utils import generate_date_keyboard, notify_admin, ENTERING_PHONE, enter_name, enter_phone
from handlers.utils import ENTERING_NAME
from handlers.utils import save_booking_to_file, delete_booking, get_taken_slots
from weather import get_weather_for_date
from yclients_api import create_yclients_booking
from datetime import datetime# добавь в начало файла, если ещё нет
from handlers.utils import is_slot_taken_yclients, load_admins
from yclients_api import get_yclients_bookings, DEFAULT_STAFF_ID
from bookings_storage import save_booking_to_file, delete_booking, get_booking, get_all_bookings


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

            # Формируем текст с погодой
            weather_text = (
                f"📅 Вы выбрали {selected_date}\n"
                f"🌡️ Температура: {weather['temp']}°C\n"
                f"💨 Ветер: {weather['wind']} м/с\n"
            )
            if weather["rain"]:
                weather_text += "🌧️ Осадки: возможны\n"

            weather_text += "\nТеперь выберите время:"

            # Клавиатура с интервалами времени
            time_slots = [
                "11:00 - 12:30",
                "13:00 - 14:30",
                "15:00 - 16:30",
                "17:00 - 18:30",
                "19:00 - 20:30",
                "21:00 - 22:30"
            ]
            staff_map = {
                "Синяя": 3813130,
                "Красная": 3811393,
                "Белая": 3819999
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
            # Возвращаем пользователя в выбор лодки
            keyboard = [
                [InlineKeyboardButton("Синяя лодка", callback_data="blue")],
                [InlineKeyboardButton("Красная лодка", callback_data="red")],
                [InlineKeyboardButton("Белая лодка", callback_data="white")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Выберите лодку:", reply_markup=reply_markup)

            # Очищаем частично введённые данные
            context.user_data.pop("user_name", None)
            context.user_data.pop("phone_number", None)
            context.user_data["state"] = None

        elif data == "back":
            # Получаем дату начала текущей недели из контекста
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
                # Обновляем состояние на предыдущую неделю
                context.user_data["current_week_start"] = prev_week_start
                keyboard = generate_date_keyboard(prev_week_start, context)
                reply_markup = keyboard
                boat = context.user_data.get("selected_boat")
                await query.edit_message_text(
                    f"Вы выбрали лодку {boat}. Теперь выберите дату:",
                    reply_markup=reply_markup
                )
# Обработка кнопки "Назад" и других кнопок
        elif data == "back_to_start":
            if context.bot_data.get(f"pending-{user_chat_id}"):
                await query.answer("⏳ Ожидайте подтверждения от администратора.")
                return
            keyboard = []
            # Если пользователь сделал запись, добавляем кнопку "Моя запись"
            if get_booking(user_chat_id):
                # Убираем кнопку "Выбор лодки", если есть запись
                keyboard.append([InlineKeyboardButton("📌 Моя запись", callback_data="my_booking")])

            # Если записи нет, показываем кнопку "Выбор лодки"
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


        # Обработка кнопки "Вперед"
        elif data == "forward":
            # Получаем дату начала текущей недели из контекста
            current_week_start = context.user_data.get("current_week_start", datetime.now().date())

            # Переходим к следующей неделе
            next_week_start = current_week_start + timedelta(days=7)
            context.user_data["current_week_start"] = next_week_start  # Обновляем состояние

            # Генерируем клавиатуру для следующей недели
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
                [InlineKeyboardButton("❌ Отмена записи", callback_data="cancel_booking")],
                [InlineKeyboardButton("🔄 Перенос записи", callback_data="reschedule_booking")],
                [InlineKeyboardButton("🏠 Выйти в меню", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(message, reply_markup=reply_markup)
        # Обработка кнопки "Отмена записи"# Отмена бронирования
        elif data == "cancel_booking":
            booking = get_booking(user_chat_id)
            if not booking:
                await query.edit_message_text("❌ У вас нет активной записи.")
                return
            boat = context.user_data.get("selected_boat", "🚤 Не выбрано")
            date = context.user_data.get("selected_date", "📅 Не выбрано")
            time = context.user_data.get("selected_time", "⏰ Не выбрано")
            user_chat_id = update.effective_user.id

            admin_message = (
                f"⚠️ Пользователь хочет отменить запись:\n"
                f"- Лодка: {boat}\n"
                f"- Дата: {date}\n"
                f"- Время: {time}\n"
                f"- Имя: {name}\n"
                f"- Телефон: {phone}"
            )

            # Удаляем локальную бронь
            delete_booking(user_chat_id)

            # Отправляем уведомление админу
            await notify_admin(context, admin_message, user_chat_id)

            # Сохраняем состояние отмены
            context.bot_data[f"pending-{user_chat_id}"] = True
            context.bot_data[f"pending_msg_id-{user_chat_id}"] = query.message.message_id
            context.bot_data[f"cancel-{user_chat_id}"] = True
            context.bot_data[f"cancel_msg_id-{user_chat_id}"] = query.message.message_id

            user_message = "❌ Вы запросили отмену записи. Администратор свяжется с Вами в ближайшее время."
            keyboard = [[InlineKeyboardButton("🏠 Выйти в меню", callback_data="back_to_start")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(user_message, reply_markup=reply_markup)


        # Перенос бронирования
        elif data == "reschedule_booking":
            booking = get_booking(user_chat_id)
            if not booking:
                await query.edit_message_text("❌ У вас нет активной записи.")
                return
            boat = context.user_data.get("selected_boat", "🚤 Не выбрано")
            date = context.user_data.get("selected_date", "📅 Не выбрано")
            time = context.user_data.get("selected_time", "⏰ Не выбрано")
            user_chat_id = update.effective_user.id

            name = context.user_data.get("user_name", "Не указано")
            phone = context.user_data.get("phone_number", "Не указано")

            admin_message = (
                f"🔄 Пользователь хочет перенести запись:\n"
                f"- Лодка: {boat}\n"
                f"- Дата: {date}\n"
                f"- Время: {time}\n"
                f"- 👤 Имя: {name}\n"
                f"- 📞 Телефон: {phone}"
            )

            delete_booking(user_chat_id)
            await notify_admin(context, admin_message, user_chat_id)

            user_message = "🔄 Вы запросили перенос записи. Администратор был уведомлен."
            keyboard = [[InlineKeyboardButton("🏠 Выйти в меню", callback_data="back_to_start")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot_data[f"reschedule-{user_chat_id}"] = True
            context.bot_data[f"reschedule_msg_id-{user_chat_id}"] = query.message.message_id
            await query.edit_message_text(user_message, reply_markup=reply_markup)

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
        
        # Проверяем, какое время выбрал пользователь
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

            # Текст с подтверждением и просьбой ввести имя
            text = (
                f"📌 Вы выбрали:\n"
                f"- Лодка: {boat}\n"
                f"- Дата: {formatted_date}\n"
                f"- Время: {selected_time}\n\n"
                f"✍️ Введите ваше имя:"
            )

            await query.edit_message_text(text=text)

            # Сохраняем message_id для дальнейших обновлений
            context.user_data["booking_message_id"] = query.message.message_id

            return ENTERING_NAME


        elif data.startswith("approve-"):
            user_chat_id = int(data.split("-")[1])
            is_reschedule = context.bot_data.get(f"reschedule-{user_chat_id}", False)
            is_cancel = context.bot_data.get(f"cancel-{user_chat_id}", False)

            if is_cancel:
                delete_booking(user_chat_id)
                context.bot_data.pop(f"cancel-{user_chat_id}", None)

                message_id = context.bot_data.pop(f"cancel_msg_id-{user_chat_id}", None)
                keyboard = [[InlineKeyboardButton("🏠 Выйти в меню", callback_data="back_to_start")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                if message_id:
                    await context.bot.edit_message_text(
                        chat_id=user_chat_id,
                        message_id=message_id,
                        text="✅ Ваша заявка успешно отменена.",
                        reply_markup=reply_markup
                    )
                else:
                    await context.bot.send_message(
                        chat_id=user_chat_id,
                        text="✅ Ваша заявка успешно отменена.",
                        reply_markup=reply_markup
                    )
                await query.edit_message_text("✅ Отмена подтверждена. Пользователь уведомлён.")
                context.bot_data.pop(f"pending-{user_chat_id}", None)
                context.bot_data.pop(f"pending_msg_id-{user_chat_id}", None)
                context.bot_data.pop(f"cancel-{user_chat_id}", None)
                context.bot_data.pop(f"cancel_msg_id-{user_chat_id}", None)
                return

            try:
                if is_reschedule:
                    # Удаляем бронь
                    delete_booking(user_chat_id)
                    context.bot_data.pop(f"reschedule-{user_chat_id}", None)

                    keyboard = [
                        [InlineKeyboardButton("🏠 Выйти в меню", callback_data="back_to_start")]
                    ]
                    # Сброс всех пользовательских данных

                    reply_markup = InlineKeyboardMarkup(keyboard)
                    message_id = context.bot_data.pop(f"reschedule_msg_id-{user_chat_id}", None)
                    if message_id:
                        await context.bot.edit_message_text(
                            chat_id=user_chat_id,
                            message_id=message_id,
                            text="✅ Ваш запрос на перенос подтверждён!\n"
                                "Ваша старая запись удалена.\n"
                                "Выберите новую лодку, чтобы создать бронь.",
                            reply_markup=reply_markup
                        )
                    else:
                        # fallback, если message_id не найден
                        await context.bot.send_message(
                            chat_id=user_chat_id,
                            text="✅ Ваш запрос на перенос подтверждён!\n"
                                "Ваша старая запись удалена.\n"
                                "Выберите новую лодку, чтобы создать бронь.",
                            reply_markup=reply_markup
                        )
                    await query.edit_message_text("✅ Перенос подтверждён. Пользователь уведомлён.")
                    return
            
                booking_data = context.bot_data.get(user_chat_id)
                if not booking_data:
                    raise ValueError("Нет данных о брони в context.bot_data")
                save_booking_to_file(user_chat_id, booking_data)
                context.bot_data.pop(f"pending-{user_chat_id}", None)
                # ⬇️ Добавляем вызов Yclients API
                try:
                    date_str = booking_data.get("selected_date")
                    time_raw = booking_data.get("selected_time")

                    if not date_str or not time_raw:
                        raise ValueError("Не хватает даты или времени для создания брони")

                    start_time = time_raw.split(" - ")[0]
                    existing = get_yclients_bookings(date_str)
                    staff_id = 3813130  # или через staff_map[boat]
                    start_time = f"{date_str}T{start_time}:00"

                    already_taken = any(
                        b.get("staff", {}).get("id") == staff_id and b.get("datetime") == start_time
                        for b in existing
                    )

                    if already_taken:
                        await context.bot.send_message(
                            chat_id=user_chat_id,
                            text="❌ Ошибка: выбранное время уже занято в системе. Пожалуйста, выберите другое время."
                        )
                        await query.edit_message_text("❌ Подтверждение отклонено. Время уже занято.")
                        return

                    # Отправляем в YCLIENTS
                    success = create_yclients_booking(
                        name=booking_data["user_name"],
                        phone=booking_data["phone_number"],
                        date=date_str,
                        boat=boat,
                        staff_id=19177301
                    )

                    if not success:
                        print("❌ Ошибка при бронировании через YCLIENTS API")

                except Exception as api_error:
                    print("⚠️ Ошибка при вызове Yclients API:", api_error)

                # Подтверждение для пользователя
                confirmed_text = (
                    f"📌 Ваша запись:\n"
                    f"- Лодка: {booking_data['selected_boat']}\n"
                    f"- Дата: {booking_data['selected_date']}\n"
                    f"- Время: {booking_data['selected_time']}\n"
                    f"- Имя: {booking_data['user_name']}\n"
                    f"- Телефон: {booking_data['phone_number']}\n"
                    f"✅ Ваша заявка одобрена администратором!"
                )


                keyboard = [[InlineKeyboardButton("🏠 Выйти в меню", callback_data="back_to_start")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                booking_message_id = context.bot_data.get(f"booking_msg_id-{user_chat_id}")

                try:
                    if booking_message_id:
                        await context.bot.edit_message_text(
                            chat_id=user_chat_id,
                            message_id=booking_message_id,
                            text=confirmed_text,
                            reply_markup=reply_markup
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=user_chat_id,
                            text=confirmed_text,
                            reply_markup=reply_markup
                        )
                except Exception as e:
                    print(f"❌ Не удалось обновить сообщение: {e}")
                context.bot_data.pop(f"pending-{user_chat_id}", None)
                await query.edit_message_text("✅ Заявка одобрена. Пользователь уведомлён.")

            except Exception as e:
                print(f"Ошибка при подтверждении и сохранении брони: {e}")
            context.bot_data.pop(f"pending-{user_chat_id}", None)

            
        elif data.startswith("reject-"):
            user_chat_id = int(data.split("-")[1])

            # Если администратор уже нажимал "Не ок", то просто удаляем запись
            if context.bot_data.get(f"reject-{user_chat_id}"):
                context.bot_data.pop(user_chat_id, None)  # Удаляем данные о брони
                context.bot_data.pop(f"reject-{user_chat_id}", None)  # Сбрасываем флаг

                try:
                    await context.bot.send_message(
                        chat_id=user_chat_id,
                        text="❌ Ваш запрос на перенос отклонён администратором. Бронь удалена."
                    )
                    await query.edit_message_text("❌ Запись удалена. Пользователь уведомлён.")
                except Exception as e:
                    print(f"Ошибка при уведомлении пользователя: {e}")
            
            # Первый раз "Не ок" → показываем детали пользователя и новые кнопки
            else:
                context.bot_data[f"reject-{user_chat_id}"] = True  # Запоминаем, что первый раз нажали "Не ок"

                user_info = f"👤 Пользователь: {user_chat_id}\n" \
                            f"🚤 Лодка: {context.bot_data.get(user_chat_id, {}).get('selected_boat', 'Неизвестно')}\n" \
                            f"📅 Дата: {context.bot_data.get(user_chat_id, {}).get('selected_date', 'Неизвестно')}\n" \
                            f"⏰ Время: {context.bot_data.get(user_chat_id, {}).get('selected_time', 'Неизвестно')}"

                keyboard = [
                    [InlineKeyboardButton("✅ Ок", callback_data=f"approve-{user_chat_id}")],
                    [InlineKeyboardButton("❌ Не ок", callback_data=f"reject-{user_chat_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    f"❌ Вы отклонили запрос на перенос. Подтвердите удаление:\n\n{user_info}",
                    reply_markup=reply_markup
                )
                    

        elif data.startswith("final_approve-"):
            user_chat_id = int(data.split("-")[1])

            try:
                await context.bot.send_message(
                    chat_id=user_chat_id,
                    text="✅ Ваш запрос на перенос подтвержден администратором. "
                         "Ваша старая запись удалена. Вы можете создать новую бронь."
                )

                await query.edit_message_text("✅ Перенос подтвержден. Пользователь уведомлен.")

            except Exception as e:
                print(f"Ошибка при уведомлении пользователя о подтверждении переноса: {e}")

        elif data.startswith("final_reject-"):
            user_chat_id = int(data.split("-")[1])

            try:
                await context.bot.send_message(
                    chat_id=user_chat_id,
                    text="❌ Ваш запрос на перенос был отклонен администратором. "
                         "Ваша старая запись остается в силе."
                )

                await query.edit_message_text("❌ Перенос окончательно отклонен. Пользователь уведомлен.")

            except Exception as e:
                print(f"Ошибка при уведомлении пользователя об отклонении переноса: {e}")
    else:
        user_input = update.message.text.strip()
        state = context.user_data.get("state")
        
        if state == ENTERING_NAME:
            await enter_name(update, context)
        elif state == ENTERING_PHONE:
            await enter_phone(update, context)
        else:
            # Если пользователь не находится в диалоге, игнорируем сообщение
            pass
