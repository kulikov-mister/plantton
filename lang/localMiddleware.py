# lang/localMiddleware.py
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from lang.translator import Translator, ROOT_LOCALE


class LangMiddleware(BaseMiddleware):
    def __init__(self, translator: Translator):
        super().__init__()
        self.translator = translator

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем язык пользователя из Telegram API
        language_code = getattr(event, 'language_code', ROOT_LOCALE)

        # Создаем переводчик на основе языка пользователя
        localized_translator = self.translator.get_translator(
            locale=language_code)

        # Добавляем переводчик в data для хендлеров
        data['translator'] = localized_translator

        return await handler(event, data)
