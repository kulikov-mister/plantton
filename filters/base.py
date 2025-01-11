# filters/base.py
from typing import Callable, Coroutine, Any, Dict
import logging
import asyncio
import re
import os
import json

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from config import bot, admin_ids_str
from db.crud import UserCRUD
from utils.bot_configs import set_bot_configs, set_commands
from lang.translator import LocalizedTranslator, Translator


# фильтр на админа
class IsAdmin(BaseFilter):
    async def __call__(self, obj: object) -> bool:
        # Определяем user_id в зависимости от типа события
        if isinstance(obj, Message) or isinstance(obj, CallbackQuery):
            user_id: int = obj.from_user.id
        else:
            return False

        if admin_ids_str:
            return user_id in admin_ids_str
        else:
            return False


# фильтр на зарегистрированного пользователя
class IsAuth(BaseFilter):
    async def __call__(self, obj: object, event_from_user, session, translator) -> bool:
        # Определяем user_id в зависимости от типа события
        if isinstance(obj, Message) or isinstance(obj, CallbackQuery):
            user_id: int = obj.from_user.id
            language_code = obj.from_user.language_code
        else:
            return False

        # Проверяем пользователя в базе данных
        user = await UserCRUD.get_user_by_user_id(session, str(user_id))

        if not user:
            # Регистрация нового пользователя
            user = await UserCRUD.create_user(session, str(user_id))

            # Установка параметров бота
            await set_bot_configs(bot, language_code)

            # Сообщение об успешной регистрации
            await obj.answer(translator.get('registration_success'))

            # Обновляем команды для существующего пользователя
            # await set_commands(bot, language_code)

        return True  # Пропускаем пользователя к хэндлеру
