# бот который создает книги и загружает их в Telegraph
from typing import Callable, Coroutine, Any, Dict
import asyncio
import logging

from aiogram import F
from handlers import router
from middlewares.db_middleware import DatabaseMiddleware
from middlewares.technical_works import TechWorksMiddleware
from middlewares.action import ChatActionMiddleware

from db.updater import sync_database
from db.crud import cache

from lang.translator import Translator
from lang.localMiddleware import LangMiddleware
from scheduler.scheduler import setup_scheduler
from config import bot, dp, owner_id


async def on_startup():
    response = await cache.load_cache_from_file()
    await bot.send_message(owner_id, response)


async def on_shutdown():
    response = await cache.save_cache_to_file()
    await bot.send_message(owner_id, response)


# стартовые настройки бота
async def main() -> None:
    # Включаем логирование
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Проверяем и обновляем структуру БД
    sync_database()
    # setup_scheduler()

    # регистрируем старт и стоп бота
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.include_router(router)
    # фильтр только на сообщения внутри чата
    dp.update.filter(F.chat.type == "private")

    # Регистрируем Middleware с передачей экземпляра Translator
    dp.update.middleware(LangMiddleware(Translator()))

    # Регистрируем Middleware отправки статуса для всех типов сразу
    dp.update.middleware(ChatActionMiddleware())

    # Регистрируем Middleware для проверки технических работ
    dp.update.middleware(TechWorksMiddleware())
    # Регистрируем Middleware для базы данных
    dp.update.middleware(DatabaseMiddleware())

    # Очистка накопленных сообщений перед стартом
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем поллинг
    await dp.start_polling(bot)


# запуск бота
if __name__ == "__main__":
    asyncio.run(main())
