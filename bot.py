# bot.py
from telegram.ext import ApplicationBuilder
from handlers.menu_handlers import start_handler, faq_handler, help_handler, back_handler
from handlers.button_handler import callback_handler
from handlers.boat_handler import boat_handler

# Основная функция для запуска бота
async def main():
    try:
        # Вставьте сюда токен вашего бота
        token = "7933616069:AAE1rIpYDIehi3h5gYFU7UQizeYhCifbFRk"
        if not token or token == "YOUR_BOT_TOKEN":
            raise ValueError("Токен бота не установлен. Пожалуйста, укажите действительный токен.")
        # Создаём приложение для бота
        application = ApplicationBuilder().token(token).build()
        # Добавляем обработчики
        application.add_handler(start_handler)
        application.add_handler(boat_handler)
        application.add_handler(callback_handler)
        application.add_handler(faq_handler)
        application.add_handler(help_handler)
        application.add_handler(back_handler)
        # Запускаем бота
        print("Бот запущен...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        # Ожидаем завершения работы бота
        print("Бот работает. Нажмите Ctrl+C для завершения.")
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем.")