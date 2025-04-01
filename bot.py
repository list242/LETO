from telegram.ext import ApplicationBuilder, CommandHandler
from handlers.button_handler import start_handler, faq_handler, help_handler, back_handler
from handlers.button_handler import callback_handler
from handlers.button_handler import boat_handler
from handlers.button_handler import register_admin
from handlers.button_handler import conv_handler, cancel
import asyncio

# Основная функция для запуска бота
async def main():
    try:
        # Вставьте сюда токен вашего бота
        token = "7933616069:AAE1rIpYDIehi3h5gYFU7UQizeYhCifbFRk"
        
        if not token or token == "YOUR_BOT_TOKEN":
            raise ValueError("Токен бота не установлен. Пожалуйста, укажите действительный токен.")

        # Создаём приложение для бота
        application = ApplicationBuilder().token(token).build()

        # Очистка очереди обновлений перед запуском
        async with application.bot:
            await application.bot.delete_webhook()  # Удаляем вебхук (если он был)
            updates = await application.bot.get_updates(offset=-1)  # Очищаем очередь обновлений
            print(f"Очищено {len(updates)} старых обновлений.")

        # Добавляем обработчики
        application.add_handler(start_handler)
        application.add_handler(boat_handler)
        application.add_handler(callback_handler)
        application.add_handler(faq_handler)
        application.add_handler(help_handler)
        application.add_handler(back_handler)
        application.add_handler(CommandHandler("register", register_admin))
        application.add_handler(conv_handler)

        # Запускаем бота
        print("Бот запущен...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        print("Бот работает. Нажмите Ctrl+C для завершения.")

        # Бесконечный цикл для поддержания работы бота
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        # Корректное завершение работы бота
        if application:
            await application.stop()
            await application.shutdown()
            print("Бот успешно остановлен.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем.")