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
from handlers.utils import load_admins, RUSSIAN_DAY_ABBREVIATIONS, ENTERING_NAME, ENTERING_PHONE, enter_name, enter_phone 
SELECTING_TIME = range(3)
ADMIN_FILE = "admins.json"

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
    keyboard = [
        [InlineKeyboardButton("🚤 Выбор лодки", callback_data="select_boat")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
        [InlineKeyboardButton("❓ Частые вопросы", callback_data="faq")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("👋 Добро пожаловать! Выберите один из пунктов ниже:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("👋 Добро пожаловать! Выберите один из пунктов ниже:", reply_markup=reply_markup)

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
        [InlineKeyboardButton("🚤 Выбор лодки", callback_data="select_boat")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
        [InlineKeyboardButton("❓ Частые вопросы", callback_data="faq")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Вы вернулись в главное меню.",
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END  # Завершаем диалог

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Процесс бронирования отменён.")
    return ConversationHandler.END  # Завершаем диалог
conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],  # Исправлено на MessageHandler
    states={
        SELECTING_TIME: [CallbackQueryHandler(handle_message)],
        ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
        ENTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)]
    },
    fallbacks=[
        CallbackQueryHandler(handle_back, pattern="^back_to_start$"),
        CommandHandler("cancel", cancel)
    ],
    per_chat=True  # Заменил на per_chat вместо per_message
)
async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📌 Частые вопросы:\n"
        "- 📅 Можно ли перенести бронь?\n"
        "- ⚓ Какие условия аренды?\n"
        "- 👶 Есть ли ограничения по возрасту?\n"
        "🔙 Для возврата в меню нажмите кнопку .",
        reply_markup=reply_markup
    )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
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
async def approve_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Получаем ID пользователя, которого подтверждает админ
    user_chat_id = int(query.data.split("-")[1])

    # Отправляем пользователю сообщение о подтверждении
    try:
        await context.bot.send_message(
            chat_id=user_chat_id,
            text="✅ Ваша заявка одобрена! Администратор подтвердил бронирование. Ждём вас!"
        )
    except Exception as e:
        print(f"Ошибка при отправке сообщения пользователю {user_chat_id}: {e}")

    # Обновляем сообщение для администратора
    await query.edit_message_text("✅ Заявка одобрена. Пользователь уведомлён.")

# Экспортируем обработчик callback-запросов
# Регистрация обработчиков
start_handler = CommandHandler("start", start)
faq_handler = CallbackQueryHandler(faq_handler, pattern="^faq$")
help_handler = CallbackQueryHandler(help_handler, pattern="^help$")
back_handler = CallbackQueryHandler(start, pattern="^back_to_start$")
callback_handler = CallbackQueryHandler(handle_message)
callback_handler2 = CallbackQueryHandler(my_booking, pattern="^my_booking$")
boat_handler = CallbackQueryHandler(choose_boat, pattern="^select_boat$")
approve_handler = CallbackQueryHandler(approve_booking, pattern="^approve-\\d+$")
