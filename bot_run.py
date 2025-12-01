import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
import config
from bot.handlers import router

# Настройка логирования
logging.basicConfig(level=logging.INFO)


async def main():
    # --- НАСТРОЙКА ПРОКСИ ---
    # УДАЛИ ИЛИ ЗАКОММЕНТИРУЙ ЭТИ СТРОКИ ДЛЯ ПРОДАКШЕНА:
    # proxy_url = "http://127.0.0.1:10809"
    # session = AiohttpSession(proxy=proxy_url)

    # ИСПОЛЬЗУЙ ПРОСТУЮ ИНИЦИАЛИЗАЦИЮ:
    bot = Bot(token=config.BOT_TOKEN) # Убрали session=session

    dp = Dispatcher()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")