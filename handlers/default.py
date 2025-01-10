# handlers/default.py
from typing import Callable, Coroutine, Any, Dict

from aiogram.filters.command import Command
from aiogram.filters import or_f
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from lang.translator import LocalizedTranslator

from config import dp
from filters.base import IsAdmin

router = Router()


class States(StatesGroup):
    config = State()


# Хэндлер на команду /privacy
@dp.message(IsAdmin(), or_f(Command("privacy"), Command("start", magic=F.args.in_('privacy'))))
async def cmd_privacy(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    privacy_url = ''
    msg = translator.get('privacy', url=privacy_url)
    await message.answer("Политика конфиденциальности")


# Хэндлер на команду /terms
@dp.message(IsAdmin(), or_f(Command("terms"), Command("start", magic=F.args.in_('terms'))))
async def cmd_privacy(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    terms_url = ''
    msg = translator.get('terms', url=terms_url)
    await message.answer("Условия использования")
