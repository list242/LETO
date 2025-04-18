Telegram 📢 бот для бронирования лодок + YCLIENTS API
🔄 Описание
Telegram-бот для бронирования проката лодок. Поддерживает интеграцию с YCLIENTS API для официального создания записей.
📂 Структура
webhook_server.py - FastAPI-сервер для webhook от YCLIENTS.
yclients_api.py - работа с YCLIENTS API: записи, поиск.
utils.py - вспомогательные функции, работа с admin/бронями.
button_handler.py - обработка кнопок Telegram.
handle_message.py - основная логика бота: выбор лодки, даты, времени, отмена, перенос.

✨ Функции
Бронирование лодок.
Провека свободных слотов.
Создание записей в YCLIENTS.
Уведомления администраторам в Telegram.
Инструктаж-викторина перед бронированием.

🌐 Запуск
Ставим зависимости:
pip install -r requirements.txt
Запуск webhook-сервера:
uvicorn webhook_server:app --host 0.0.0.0 --port 8000
Развернуть бота Telegram.

🔧 Переменные окружения
USER_TOKEN - токен пользователя YCLIENTS
PARTNER_TOKEN - партнерский токен
X_PARTNER_ID - ID партнера
COMPANY_ID, DEFAULT_STAFF_ID, SERVICE_ID - данные компании YCLIENTS

📥 Локальные файлы
admins.json - chat_id админов
bookings.json - брони с телеграм
yclients_token.txt - актуальный User Token

📍 Проект готов для деплоя на Railway, Render или VPS.
