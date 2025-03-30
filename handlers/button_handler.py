import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime, timedelta
import calendar
ADMIN_FILE = "admins.json"
# Максимальная дата для выбора
def load_admins():
    try:
        with open(ADMIN_FILE, "r", encoding="utf-8") as file:
            return set(json.load(file))
    except FileNotFoundError:
        return set()

# Функция для сохранения chat_id администраторов в файл
def save_admins(admin_chat_ids):
    with open(ADMIN_FILE, "w", encoding="utf-8") as file:
        json.dump(list(admin_chat_ids), file, ensure_ascii=False, indent=4)

# Глобальная переменная для хранения chat_id администраторов
admin_chat_ids = load_admins()

MAX_DATE = datetime(2025, 8, 31).date()
# Словарь для хранения chat_id администраторов
admin_chat_ids = set()
# Русские аббревиатуры дней недели
RUSSIAN_DAY_ABBREVIATIONS = {0: "Пн",1: "Вт",2: "Ср",3: "Чт",4: "Пт",5: "Сб",6: "Вс"}

# Функция для форматирования даты в нужном формате
def format_date(date):
    day_name = RUSSIAN_DAY_ABBREVIATIONS[date.weekday()]  # Например, "Пн", "Вт", "Ср"
    return f"{date.strftime('%d.%m.%Y')} ({day_name})"

# Функция для генерации клавиатуры с датами
def generate_date_keyboard(start_date, context):
    keyboard = []
    current_date = start_date + timedelta(days=1)  # Начинаем с завтрашнего дня
    days_shown = 0

    # Для текущей недели: отображаем дни до конца недели (включая воскресенье)
    if start_date == datetime.now().date():
        while days_shown < 7 and current_date.weekday() != calendar.SUNDAY and current_date <= MAX_DATE:
            date_str = format_date(current_date)  # Отображаемый текст: DD.MM.YYYY (день недели)
            callback_data = f"date-{current_date.isoformat()}"  # Callback-данные: YYYY-MM-DD
            keyboard.append([InlineKeyboardButton(date_str, callback_data=callback_data)])
            current_date += timedelta(days=1)
            days_shown += 1

        # Добавляем воскресенье
        if current_date.weekday() == calendar.SUNDAY and current_date <= MAX_DATE:
            date_str = format_date(current_date)  # Отображаемый текст: DD.MM.YYYY (день недели)
            callback_data = f"date-{current_date.isoformat()}"  # Callback-данные: YYYY-MM-DD
            keyboard.append([InlineKeyboardButton(date_str, callback_data=callback_data)])

    # Для следующих недель: отображаем полные 7 дней или до MAX_DATE
    else:
        # Убедимся, что текущая дата является понедельником
        if current_date.weekday() != 0:  # Если не понедельник, перейти к следующему понедельнику
            days_until_monday = (7 - current_date.weekday()) % 7
            current_date += timedelta(days=days_until_monday)

        for _ in range(7):
            if current_date > MAX_DATE:
                break  # Прекращаем добавление дат, если достигнута максимальная дата
            date_str = format_date(current_date)  # Отображаемый текст: DD.MM.YYYY (день недели)
            callback_data = f"date-{current_date.isoformat()}"  # Callback-данные: YYYY-MM-DD
            keyboard.append([InlineKeyboardButton(date_str, callback_data=callback_data)])
            current_date += timedelta(days=1)

    # Если достигнута максимальная дата, кнопка "Вперед" не добавляется
    if current_date > MAX_DATE:
        keyboard.append([InlineKeyboardButton("Назад", callback_data="back")])
    else:
        keyboard.append([InlineKeyboardButton("Назад", callback_data="back")])
        keyboard.append([InlineKeyboardButton("Вперед", callback_data="forward")])
    return InlineKeyboardMarkup(keyboard)
async def start(update: Update, context):
    user_name = update.message.from_user.first_name
    await update.message.reply_text(f"Привет, {user_name}! Я бот для бронирования лодок.")

# Обработчик команды /register для регистрации администраторов
async def register_admin(update: Update, context):
    chat_id = update.message.chat_id
    if chat_id in admin_chat_ids:
        await update.message.reply_text("Вы уже зарегистрированы как администратор.")
    else:
        admin_chat_ids.add(chat_id)
        save_admins(admin_chat_ids)
        await update.message.reply_text(f"Вы зарегистрированы как администратор. Ваш chat_id: {chat_id}")

async def notify_admin(context, message, user_chat_id):
    for admin_chat_id in admin_chat_ids:
        try:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Ок", callback_data=f"approve-{user_chat_id}"),
                    InlineKeyboardButton("❌ Не ок", callback_data=f"reject-{user_chat_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(chat_id=admin_chat_id, text=message, reply_markup=reply_markup)
            print(f"Уведомление отправлено администратору с chat_id: {admin_chat_id}")
        except Exception as e:
            print(f"Ошибка при отправке уведомления администратору с chat_id {admin_chat_id}: {e}")

async def my_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    boat = context.user_data.get("selected_boat", "🚤 Не выбрано")
    date = context.user_data.get("selected_date", "📅 Не выбрано")
    time = context.user_data.get("selected_time", "⏰ Не выбрано")

    message = f"🔹 Ваша запись:\n- Лодка: {boat}\n- Дата: {date}\n- Время: {time}"
    
    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, reply_markup=reply_markup)

# Функция для обработки текстовых сообщений и callback-запросов
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    # Если это callback (нажатие на кнопку)
    if query:
        await query.answer()  # Подтверждаем получение callback
        data = query.data

        # Проверяем, какую лодку выбрал пользователь
        if data in ["blue", "red", "white"]:
            selected_boat = {
                "blue": "Синяя",
                "red": "Красная",
                "white": "Белая"
            }[data]
            context.user_data["selected_boat"] = selected_boat

            # Сохраняем дату начала текущей недели
            today = datetime.now().date()
            context.user_data["current_week_start"] = today

            # Генерируем клавиатуру с датами
            keyboard = generate_date_keyboard(today, context)
            reply_markup = keyboard

            # Обновляем сообщение с кнопками
            await query.edit_message_text(
                f"Вы выбрали лодку {selected_boat}. Теперь выберите дату:",
                reply_markup=reply_markup
            )

        # Проверяем, какую дату выбрал пользователь
        elif data.startswith("date-"):
            selected_date = data.replace("date-", "", 1)
            # Проверяем, что дата является строкой в формате ISO (YYYY-MM-DD)
            try:
                datetime.fromisoformat(selected_date)  # Проверка формата
                context.user_data["selected_date"] = selected_date
            except ValueError:
                await query.edit_message_text("Некорректный формат даты. Пожалуйста, попробуйте снова.")
                return

            # Создаём кнопки со временными слотами
            time_slots = [
                "11:00 - 12:30",
                "13:00 - 14:30",
                "15:00 - 16:30",
                "17:00 - 18:30",
                "19:00 - 20:30",
                "21:00 - 22:30"
            ]

            keyboard = []
            keyboard = [[InlineKeyboardButton(slot, callback_data=f"time-{slot}")] for slot in time_slots]
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Обновляем сообщение с временными слотами
            await query.edit_message_text(
                f"Вы выбрали дату {selected_date}. Теперь выберите время:",
                reply_markup=reply_markup
            )

        # Обработка кнопки "Назад"
        elif data == "back":
            # Получаем дату начала текущей недели из контекста
            current_week_start = context.user_data.get("current_week_start", datetime.now().date())
            prev_week_start = current_week_start - timedelta(days=7)
            if prev_week_start < datetime.now().date():
                keyboard = [
                    [InlineKeyboardButton("Синяя", callback_data="blue")],
                    [InlineKeyboardButton("Красная", callback_data="red")],
                    [InlineKeyboardButton("Белая", callback_data="white")]
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
            keyboard = []

            # Если пользователь сделал запись, добавляем кнопку "Моя запись"
            if "selected_boat" in context.user_data and "selected_date" in context.user_data and "selected_time" in context.user_data:
                # Убираем кнопку "Выбор лодки", если есть запись
                keyboard.append([InlineKeyboardButton("📌 Моя запись", callback_data="my_booking")])

            # Если записи нет, показываем кнопку "Выбор лодки"
            else:
                keyboard.append([InlineKeyboardButton("🚤 Выбор лодки", callback_data="select_boat")])

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
            boat = context.user_data.get("selected_boat", "🚤 Не выбрано")
            date = context.user_data.get("selected_date", "📅 Не выбрано")
            time = context.user_data.get("selected_time", "⏰ Не выбрано")

            message = f"📌 Ваша запись:\n- Лодка: {boat}\n- Дата: {date}\n- Время: {time}"

            keyboard = [
                [InlineKeyboardButton("❌ Отмена записи", callback_data="cancel_booking")],
                [InlineKeyboardButton("🔄 Перенос записи", callback_data="reschedule_booking")],
                [InlineKeyboardButton("🏠 Выйти в меню", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(message, reply_markup=reply_markup)
        # Обработка кнопки "Отмена записи"# Отмена бронирования
        elif data == "cancel_booking":
            boat = context.user_data.get("selected_boat", "🚤 Не выбрано")
            date = context.user_data.get("selected_date", "📅 Не выбрано")
            time = context.user_data.get("selected_time", "⏰ Не выбрано")
            user_chat_id = update.effective_user.id

            admin_message = (
                f"⚠️ Пользователь хочет отменить запись:\n"
                f"- Лодка: {boat}\n"
                f"- Дата: {date}\n"
                f"- Время: {time}"
            )

            await notify_admin(context, admin_message, user_chat_id)

            user_message = "❌ Вы запросили отмену записи. Администратор был уведомлен."
            keyboard = [[InlineKeyboardButton("🏠 Выйти в меню", callback_data="back_to_start")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(user_message, reply_markup=reply_markup)

        # Перенос бронирования
        elif data == "reschedule_booking":
            boat = context.user_data.get("selected_boat", "🚤 Не выбрано")
            date = context.user_data.get("selected_date", "📅 Не выбрано")
            time = context.user_data.get("selected_time", "⏰ Не выбрано")
            user_chat_id = update.effective_user.id

            admin_message = (
                f"🔄 Пользователь хочет перенести запись:\n"
                f"- Лодка: {boat}\n"
                f"- Дата: {date}\n"
                f"- Время: {time}"
            )

            await notify_admin(context, admin_message, user_chat_id)

            user_message = "🔄 Вы запросили перенос записи. Администратор был уведомлен."
            keyboard = [[InlineKeyboardButton("🏠 Выйти в меню", callback_data="back_to_start")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

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
            selected_time = data.replace("time-", "", 1)
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

            # Сохраняем выбранное время
            context.user_data["selected_time"] = selected_time

            keyboard = [[InlineKeyboardButton("🏠 Выйти в меню", callback_data="back_to_start")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"Ваш выбор:\n"
                f"- Лодка: {boat}\n"
                f"- Дата: {formatted_date}\n"
                f"- Время: {selected_time}",
                reply_markup=reply_markup
            )
        elif data.startswith("approve-"):
            user_chat_id = int(data.split("-")[1])

            try:
                # Очистка данных пользователя
                context.bot_data.pop(user_chat_id, None)

                # Обновляем сообщение пользователя
                keyboard = [[InlineKeyboardButton("🚤 Выбор лодки", callback_data="select_boat")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await context.bot.send_message(
                    chat_id=user_chat_id,
                    text="✅ Ваш запрос на перенос подтвержден администратором. Ваша старая запись удалена. "
                        "Теперь выберите новую лодку и создайте новую бронь.",
                    reply_markup=reply_markup
                )

                await query.edit_message_text("✅ Перенос подтвержден. Пользователь уведомлен.")

            except Exception as e:
                print(f"Ошибка при уведомлении пользователя о подтверждении переноса: {e}")
        
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


# Экспортируем обработчик callback-запросов
callback_handler = CallbackQueryHandler(handle_message)
callback_handler2 = CallbackQueryHandler(my_booking, pattern="^my_booking$")
