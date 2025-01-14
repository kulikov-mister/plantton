# middlewares/technical_works.py
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, PollAnswer
from aiogram.types import TelegramObject

from lang.translator import LocalizedTranslator

from config import admin_ids, is_tech_works


class TechWorksMiddleware(BaseMiddleware):
    """
    Middleware для проверки, находится ли бот на техническом обслуживании.
    Если включено, отправляет сообщение пользователям (кроме админов).
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        # Получаем зависимости
        translator: LocalizedTranslator = data.get("translator")
        bot: Bot = data.get("bot")

        # Определяем user_id в зависимости от типа события
        user_id: int = None

        if isinstance(event, Message):  # Обычное сообщение
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):  # Inline кнопки
            user_id = event.from_user.id
        elif isinstance(event, PreCheckoutQuery):  # Запрос перед оплатой
            user_id = event.from_user.id
        elif isinstance(event, PollAnswer):  # Ответ на опрос
            user_id = event.user.id

        # Если user_id не определен — пропускаем мидлварь
        if user_id is None:
            return await handler(event, data)

        # Проверка, находится ли бот в режиме техобслуживания
        if (not is_tech_works) or user_id in admin_ids:
            # Если не техработы или пользователь админ — пропускаем дальше
            return await handler(event, data)
        else:
            # Отправляем сообщение о техработах
            message_text: str = translator.get("tech_works_message_enabled")
            if isinstance(event, Message):
                await event.answer(message_text)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(message_text)
            elif isinstance(event, PreCheckoutQuery):
                await bot.send_message(chat_id=user_id, text=message_text)

            # Прерываем выполнение хендлера
            return
