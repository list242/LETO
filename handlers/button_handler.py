import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from datetime import datetime, timedelta
import calendar
#from handlers.handle_message import handle_message
#from handlers.utils import generate_date_keyboard, notify_admin, MAX_DATE, enter_name, enter_phone, handle_message
#from handlers.handle_message import handle_message  # ✅ Больше нет циклического импорта!
from handlers.handle_message import handle_message
  # ✅ Правильный импорт 
from bookings_storage import save_booking_to_file, delete_booking, get_booking, get_all_bookings
from handlers.utils import load_admins, RUSSIAN_DAY_ABBREVIATIONS, ENTERING_NAME, ENTERING_PHONE, enter_name, enter_phone, get_taken_slots
SELECTING_TIME = range(3)
ADMIN_FILE = "admins.json"
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

quiz_questions = [
    {"question": "🦺 Нужно ли надевать спасательный жилет перед выходом?", "options": ["Да, я же не рыба", "Нет, я бессмертный"], "correct": 0},
    {"question": "🍺 Можно ли пить пиво за рулем лодки?", "options": ["Нет, это опасно", "Да, и капитанский ром тоже"], "correct": 0},
    {"question": "🚤 Если хочешь повернуть направо, куда крутить руль?", "options": ["Направо", "Налево (логика же)"], "correct": 0},
    {"question": "📵 Когда можно пользоваться телефоном?", "options": ["Когда не управляю", "Всегда, я тиктокер"], "correct": 0},
    {"question": "💥 Если лодка не заводится?", "options": ["Позвонить администратору", "Пнуть мотор посильнее"], "correct": 0},
    {"question": "🌊 Сколько минимум метров держаться от берега?", "options": ["20 метров", "2 метра, чтоб всем видно было"], "correct": 0},
    {"question": "🧒 Можно ли катать детей без жилета?", "options": ["Нет, всегда с жилетом", "Да, пусть закаляются"], "correct": 0},
    {"question": "🧭 Потерялся. Что делать?", "options": ["Связаться по рации/телефону", "Орать в небо"], "correct": 0},
    {"question": "⚓ Что делать при сильном ветре и волнах?", "options": ["Вернуться на базу", "Гнать ещё быстрее!"], "correct": 0},
    {"question": "🧠 Инструктаж нужен для чего?", "options": ["Чтобы не попасть на бабки", "Чтоб было что скинуть друзьям"], "correct": 0}
]


def save_admins(admin_chat_ids):
    with open(ADMIN_FILE, "w", encoding="utf-8") as file:
        json.dump(list(admin_chat_ids), file, ensure_ascii=False, indent=4)

admin_chat_ids = load_admins()
#admin_chat_ids = set()
#RUSSIAN_DAY_ABBREVIATIONS = {0: "Пн",1: "Вт",2: "Ср",3: "Чт",4: "Пт",5: "Сб",6: "Вс"}

def format_date(date):
    day_name = RUSSIAN_DAY_ABBREVIATIONS[date.weekday()]  
    return f"{date.strftime('%d.%m.%Y')} ({day_name})"


async def start(update: Update, context):
    user_name = update.message.from_user.first_name
    await update.message.reply_text(f"Привет, {user_name}! Я бот для бронирования лодок.")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chat_id = update.effective_user.id
    # ❗ Проверка: если есть активный запрос (перенос, отмена, ожидание)
    admins = load_admins()
    if user_chat_id not in admins and context.bot_data.get(f"pending-{user_chat_id}"):

        if update.message:
            await update.message.reply_text("⏳ Ожидайте подтверждения от администратора.")
        elif update.callback_query:
            await update.callback_query.answer("⏳ Ожидайте подтверждения от администратора.", show_alert=True)
        return

    keyboard = [
    [InlineKeyboardButton("🚤 Выбор лодки", callback_data="select_boat")],
    [InlineKeyboardButton("📷 Фото лодок", callback_data="show_boat_photos")],
    [InlineKeyboardButton("📘 Пройти инструктаж", callback_data="start_quiz")]
    # [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
    # [InlineKeyboardButton("❓ Частые вопросы", callback_data="faq")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Добрый день, на связи cbrental🚩\nВыберите один из пунктов ниже, мы ответим на все ваши вопросы💫", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Добрый день, на связи cbrental🚩\nВыберите один из пунктов ниже, мы ответим на все ваши вопросы💫", reply_markup=reply_markup)

async def register_admin(update: Update, context):
    chat_id = update.message.chat_id
    if chat_id in admin_chat_ids:
        await update.message.reply_text("Вы уже зарегистрированы как администратор.")
    else:
        admin_chat_ids.add(chat_id)
        save_admins(admin_chat_ids)
        await update.message.reply_text(f"Вы зарегистрированы как администратор. Ваш chat_id: {chat_id}")

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

async def my_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_chat_id = update.effective_user.id
    booking = get_booking(user_chat_id)
    if not booking:
        await query.edit_message_text("❌ У вас нет активной записи.")
        return
    await query.answer()
    boat = context.user_data.get("selected_boat", "🚤 Не выбрано")
    date = context.user_data.get("selected_date", "📅 Не выбрано")
    time = context.user_data.get("selected_time", "⏰ Не выбрано")
    message = f"🔹 Ваша запись:\n- Лодка: {boat}\n- Дата: {date}\n- Время: {time}"
    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup)

async def choose_boat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
    [InlineKeyboardButton("Синяя лодка", callback_data="blue")],
    [InlineKeyboardButton("Красная лодка", callback_data="red")],
    [InlineKeyboardButton("Белая лодка", callback_data="white")],
    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Выберите лодку:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.edit_message_text("Выберите лодку:", reply_markup=reply_markup)

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Возвращаем пользователя в главное меню
    keyboard = [
        [InlineKeyboardButton("🚤 Выбор лодки", callback_data="select_boat")]
        # [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
        # [InlineKeyboardButton("❓ Частые вопросы", callback_data="faq")],
        # [InlineKeyboardButton("🤖 Нейросеть",     callback_data="qa_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Вы вернулись в главное меню.",
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END  # Завершаем диалог

# async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text("Процесс бронирования отменён.")
#     return ConversationHandler.END  # Завершаем диалог
# conv_handler = ConversationHandler(
#     entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],  # Исправлено на MessageHandler
#     states={
#         SELECTING_TIME: [CallbackQueryHandler(handle_message)],
#         ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
#         ENTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)]
#     },
#     fallbacks=[
#         CallbackQueryHandler(handle_back, pattern="^back_to_start$"),
#         CommandHandler("cancel", cancel)
#     ],
#     per_chat=True  # Заменил на per_chat вместо per_message
# )
# async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await query.edit_message_text(
#         "📌 Частые вопросы:\n"
#         "- 📅 Можно ли перенести бронь?\n"
#         "- ⚓ Какие условия аренды?\n"
#         "- 👶 Есть ли ограничения по возрасту?\n"
#         "🔙 Для возврата в меню нажмите кнопку .",
#         reply_markup=reply_markup
#     )

# async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await query.edit_message_text(
#         "❓ Раздел помощи:\n"
#         "1️⃣ Как забронировать лодку?\n"
#         "2️⃣ Какие есть правила пользования лодкой?\n"
#         "3️⃣ Как отменить бронь?\n"
#         "🔙 Для возврата в меню нажмите кнопку ниже.",
#         reply_markup=reply_markup
#     )
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["quiz_step"] = 0
    await send_quiz_question(update, context)

async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("quiz_step", 0)
    question_data = quiz_questions[step]

    buttons = [
        InlineKeyboardButton(text=opt, callback_data=f"quiz_{step}_{i}")
        for i, opt in enumerate(question_data["options"])
    ]
    keyboard = InlineKeyboardMarkup.from_row(buttons)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=question_data["question"],
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            text=question_data["question"],
            reply_markup=keyboard
        )

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # например "quiz_0_1"

    try:
        _, step_str, answer_str = data.split("_")
        step = int(step_str)
        answer = int(answer_str)

        correct_answer = quiz_questions[step]["correct"]

        # Считаем правильные ответы
        if "quiz_correct" not in context.user_data:
            context.user_data["quiz_correct"] = 0
        if answer == correct_answer:
            context.user_data["quiz_correct"] += 1

        step += 1
        if step < len(quiz_questions):
            context.user_data["quiz_step"] = step
            await send_quiz_question(update, context)
        else:
            correct_count = context.user_data["quiz_correct"]
            total = len(quiz_questions)

            if correct_count >= 8:
                text = (
                    f"🎉 Поздравляем! Вы ответили правильно на {correct_count} из {total} вопросов.\n"
                    "Вы успешно прошли инструктаж! 🚤"
                )
            else:
                text = (
                    f"⚠️ Вы ответили правильно только на {correct_count} из {total} вопросов.\n"
                    "Советуем пройти инструктаж ещё раз."
                )

            keyboard = [
                [InlineKeyboardButton("🔁 Пройти снова", callback_data="start_quiz")],
                [InlineKeyboardButton("🏠 В меню", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
            context.user_data.pop("quiz_correct", None)  # сбрасываем после окончания

    except Exception as e:
        print("Ошибка в handle_quiz_answer:", e)
        await query.edit_message_text("⚠️ Произошла ошибка при обработке ответа.")


async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = context.user_data["quiz_answers"]
    right = sum(1 for _, is_right in results if is_right)
    wrong = len(results) - right

    result_text = (
        f"✅ Правильных ответов: {right}\n"
        f"❌ Неправильных: {wrong}\n\n"
    )

    if wrong == 0:
        result_text += "🎉 Отлично! Теперь я точно не попаду на бабки!"
    else:
        result_text += "📘 Попробуй пройти инструктаж ещё раз, чтобы не попасть на бабки."

    keyboard = [[InlineKeyboardButton("🏠 В меню", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(result_text, reply_markup=reply_markup)
# Экспортируем обработчик callback-запросов
# Регистрация обработчиков
start_handler = CommandHandler("start", start)
# faq_handler = CallbackQueryHandler(faq_handler, pattern="^faq$")
# help_handler = CallbackQueryHandler(help_handler, pattern="^help$")
#back_handler = CallbackQueryHandler(start, pattern="^back_to_start$")
callback_handler = CallbackQueryHandler(handle_message)
callback_handler2 = CallbackQueryHandler(my_booking, pattern="^my_booking$")
boat_handler = CallbackQueryHandler(choose_boat, pattern="^select_boat$")
#approve_handler = CallbackQueryHandler(approve_booking, pattern="^approve-\\d+$")
