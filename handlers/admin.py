# handlers/admin.py
from typing import List, Tuple, Any

from aiogram.filters.command import Command
from aiogram.filters import or_f
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, ChosenInlineResult, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder

from filters.base import IsAdmin, IsAuth
from keyboards.inline_builder import get_paginated_keyboard

from lang.translator import LocalizedTranslator
from db.crud import UserCRUD, PaymentCRUD, BookCRUD, CategoryCRUD

from config import dp, bot, admin_ids, admin_ids_str, base_dir
from utils.telegram import send_message_admin

router = Router()
# установка единых фильтров на админа
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())
# router.inline_query.filter(IsAdmin())


class States(StatesGroup):
    set_category_name = State()


# ----------------------------------- добавить категорию -------------------------------------- #


# Хэндлер на команду /add_category
@router.message(Command("add_category"))
async def cmd_add_category(message: Message, state: FSMContext, translator: LocalizedTranslator):
    await message.answer_sticker('CAACAgEAAxkBAAIB-md1m0AGoO0FAVGqn9DIXWMSozJoAAJ_AwACjrnpRxz1DWc-DE2ZNgQ')
    await message.answer('Привет! тут тестовое сообщение')
