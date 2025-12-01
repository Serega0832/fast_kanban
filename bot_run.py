import asyncio
import logging
from aiogram import Bot, Dispatcher
import config
from bot.handlers import router

# Настройка логирования
logging.basicConfig(level=logging.INFO)


async def main():
    # Инициализируем бота (напрямую, без прокси)
    bot = Bot(token=config.BOT_TOKEN)

    dp = Dispatcher()

    # Подключаем роутер с хендлерами
    dp.include_router(router)

    print(f"🚀 Бот {config.bot_name} запускается...")

    # Удаляем старые сообщения и запускаем
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")