# middlewares/action.py
from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.dispatcher.flags import get_flag
from aiogram.utils.chat_action import ChatActionSender


class ChatActionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        chat_action = get_flag(data, "chat_action")

        # Если такого флага на хэндлере нет
        if not chat_action:
            return await handler(event, data)

        # Если флаг есть
        async with ChatActionSender(
            bot=data['bot'],
            action=chat_action,
            chat_id=event.chat.id
        ):
            return await handler(event, data)
