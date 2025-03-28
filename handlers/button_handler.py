from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from datetime import datetime, timedelta
import calendar

# Максимальная дата для выбора
MAX_DATE = datetime(2025, 8, 31).date()

# Русские аббревиатуры дней недели
RUSSIAN_DAY_ABBREVIATIONS = {
    0: "Пн",
    1: "Вт",
    2: "Ср",
    3: "Чт",
    4: "Пт",
    5: "Сб",
    6: "Вс"
}

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
            for slot in time_slots:
                keyboard.append([InlineKeyboardButton(slot, callback_data=f"time-{slot}")])
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

            # Переходим к предыдущей неделе
            prev_week_start = current_week_start - timedelta(days=7)

            # Проверяем, если мы достигли текущей недели
            if prev_week_start < datetime.now().date():
                # Возвращаемся к выбору лодки
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

                # Генерируем клавиатуру для предыдущей недели
                keyboard = generate_date_keyboard(prev_week_start, context)
                reply_markup = keyboard

                boat = context.user_data.get("selected_boat")
                await query.edit_message_text(
                    f"Вы выбрали лодку {boat}. Теперь выберите дату:",
                    reply_markup=reply_markup
                )
        elif data == "back_to_start":
            keyboard = [
                [InlineKeyboardButton("📌 Моя запись", callback_data="my_booking")],
                [InlineKeyboardButton("🚤 Выбор лодки", callback_data="select_boat")],
                [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
                [InlineKeyboardButton("❓ Частые вопросы", callback_data="faq")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("👋 Добро пожаловать! Выберите один из пунктов ниже:", reply_markup=reply_markup)

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
            selected_time = data.split("-")[1]
            boat = context.user_data.get("selected_boat")
            date = context.user_data.get("selected_date")

            # Проверяем, что дата существует и является строкой
            if not date or not isinstance(date, str):
                await query.edit_message_text("Произошла ошибка при выборе даты. Пожалуйста, попробуйте снова.")
                return

            try:
                # Преобразуем дату в формат DD.MM.YYYY
                formatted_date = datetime.fromisoformat(date).strftime('%d.%m.%Y')
            except ValueError:
                await query.edit_message_text("Некорректный формат даты. Пожалуйста, попробуйте снова.")
                return

            # Отправляем подтверждение
            await query.edit_message_text(
                f"Ваш выбор:\n"
                f"- Лодка: {boat}\n"
                f"- Дата: {formatted_date}\n"
                f"- Время: {selected_time}"
            )

# Экспортируем обработчик callback-запросов
callback_handler = CallbackQueryHandler(handle_message)
callback_handler2 = CallbackQueryHandler(my_booking, pattern="^my_booking$")
