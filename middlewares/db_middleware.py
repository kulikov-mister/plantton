# middlewares/db_middleware.py
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject
from db.models import SessionLocal


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict
    ):
        # Создаем сессию
        session = SessionLocal()
        try:
            # Добавляем сессию в data для доступа в хэндлерах
            data["session"] = session
            return await handler(event, data)
        finally:
            # Закрываем сессию после обработки хэндлера
            session.close()
