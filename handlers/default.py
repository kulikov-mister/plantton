# handlers/default.py
from typing import Callable, Coroutine, Any, Dict

from aiogram.filters.command import Command
from aiogram.filters import or_f
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from lang.translator import LocalizedTranslator

from filters.base import IsAuth

router = Router()


class States(StatesGroup):
    config = State()


# Хэндлер на команду /start
@router.message(IsAuth(), Command("start", magic=F.args.in_([None, 'start'])))
async def cmd_start(message: Message, state: FSMContext, translator: LocalizedTranslator):
    await message.answer_sticker('CAACAgEAAxkBAAIB-md1m0AGoO0FAVGqn9DIXWMSozJoAAJ_AwACjrnpRxz1DWc-DE2ZNgQ')
    # приветственное сообщение
    await message.answer(translator.get('greeting_message'), disable_web_page_preview=True)


# Хэндлер на команду /help
@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext, translator: LocalizedTranslator):
    await message.answer_sticker('CAACAgEAAxkBAAICb2d10F22KTmOyD4JeR29YEdb1Bo4AAIiAwACZr6hRjnro5jznq9LNgQ')
    await message.answer(translator.get('help_message'))


# Хэндлер на команду /privacy
@router.message(or_f(Command("privacy"), Command("start", magic=F.args.in_('privacy'))))
async def cmd_privacy(message: Message, state: FSMContext, translator: LocalizedTranslator):
    privacy_url = ''
    msg = translator.get('privacy', url=privacy_url)
    await message.answer("Политика конфиденциальности")


# Хэндлер на команду /terms
@router.message(or_f(Command("terms"), Command("start", magic=F.args.in_('terms'))))
async def cmd_terms(message: Message, state: FSMContext, translator: LocalizedTranslator):
    terms_url = ''
    msg = translator.get('terms', url=terms_url)
    await message.answer("Условия использования")
