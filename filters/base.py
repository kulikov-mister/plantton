# filters/base.py
from typing import Callable, Coroutine, Any, Dict


import logging
import asyncio
import re
import os
import json

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery, InlineQuery

from config import bot, admin_ids_str
from db.crud import UserCRUD
from utils.bot_configs import set_bot_configs


# фильтр на админа
class IsAdmin(BaseFilter):
    async def __call__(self, obj: object) -> bool:
        # Определяем user_id в зависимости от типа события
        if isinstance(obj, Message) or isinstance(obj, CallbackQuery) or isinstance(obj, InlineQuery):
            user_id: int = obj.from_user.id
        else:
            return False

        if admin_ids_str:
            return user_id in admin_ids_str
        else:
            return False


# фильтр на зарегистрированного пользователя
class IsAuth(BaseFilter):
    # Параметр, который можно передавать при использовании фильтра
    def __init__(self, check_balance: int = None):
        super().__init__()
        self.check_balance: int = check_balance

    async def __call__(self, obj: object, session, translator) -> bool:
        # Определяем user_id в зависимости от типа события
        if isinstance(obj, Message):
            user_id: int = obj.chat.id
            language_code = obj.from_user.language_code
            data_str = obj.text
        elif isinstance(obj, CallbackQuery):
            user_id: int = obj.chat.id
            language_code = obj.from_user.language_code
            data_str = obj.data
        elif isinstance(obj, InlineQuery):
            user_id: int = obj.from_user.id
            language_code = obj.from_user.language_code
            data_str = obj.query
        else:
            return False

        logging.info(f"IsAuth filter called for user_id: {
                     user_id} | text: {data_str}")

        # Проверяем пользователя в базе данных
        user = await UserCRUD.get_user_by_user_id(session, user_id)
        if not user:
            user = await UserCRUD.create_user(session, str(user_id))
            await set_bot_configs(bot, language_code)
            bot_name = await bot.get_my_name(language_code)
            await obj.answer(translator.get('registration_success', bot_name=bot_name.name))

        # Если указан для проверки баланс
        if self.check_balance:
            if user.balance <= self.check_balance:
                # Сообщение о низком балансе
                pro = 'Pro' if user.pro else 'Free' if user.pro else 'None'
                msg = translator.get('low_balance', limit=str(
                    self.check_balance), balance=user.balance, pro=pro)
                await obj.answer(msg)
                return False

        return True  # Пропускаем пользователя к хендлеру
