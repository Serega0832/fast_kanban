# --- START OF FILE: bot_run.py ---
print("DEBUG: 1. Скрипт начал работу (до импортов)")
import sys
import asyncio
import logging
import traceback

# Оборачиваем импорты, так как ошибка может быть в config или aiogram
try:
    print("DEBUG: 2. Импортируем библиотеки...")
    from aiogram import Bot, Dispatcher
    import config
    from bot.handlers import router

    print(f"DEBUG: 3. Импорты успешны. Токен: {config.BOT_TOKEN[:5]}***")
except Exception as e:
    print("CRITICAL ERROR во время импорта:")
    traceback.print_exc()
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO)


async def main():
    print("DEBUG: 4. Зашли в функцию main")
    try:
        # Инициализируем бота
        print("DEBUG: 5. Создаем объект Bot...")
        bot = Bot(token=config.BOT_TOKEN)

        dp = Dispatcher()
        dp.include_router(router)

        print("DEBUG: 6. Удаляем вебхук...")
        await bot.delete_webhook(drop_pending_updates=True)

        print("🚀 DEBUG: 7. Запускаем polling...")
        await dp.start_polling(bot)
    except Exception as e:
        print("CRITICAL ERROR внутри main:")
        traceback.print_exc()


if __name__ == "__main__":
    print("DEBUG: 0. Запуск блока __main__")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
    except Exception as e:
        print("CRITICAL ERROR при запуске asyncio:")
        traceback.print_exc()
# --- END OF FILE: bot_run.py ---