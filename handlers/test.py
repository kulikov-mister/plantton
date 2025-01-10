# handlers/test.py
from typing import Callable, Coroutine, Any, Dict
import logging
import asyncio
import re
import os
import json

from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import Command
from aiogram.filters import BaseFilter
from aiogram import Bot, Dispatcher, F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.strategy import FSMStrategy
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest

from lang.translator import LocalizedTranslator
from main import generate_topics_book, generate_book
from db.crud import UserCRUD, PaymentCRUD, BookCRUD, CategoryCRUD
from utils.telegram import send_message_admin

from config import dp, bot, admin_ids, admin_ids_str, base_dir
from filters.base import IsAdmin

router = Router()


class States(StatesGroup):
    set_test = State()
    set_payment = State()
    confirm_topics = State()
    confirm_chapters = State()


# отработка  тест стикеров
@router.message(IsAdmin(), F.sticker)
async def message_sticker_test(message: Message, state: FSMContext, translator: LocalizedTranslator):
    await state.clear()
    await message.answer(message.sticker.file_id)


# Хэндлер на команду /test
@dp.message(IsAdmin(), Command("test"))
async def cmd_test(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    await state.set_state(States.set_test)
    await message.answer("<b>Платёж создан! в бд</b>")


# Хэндлер на команду /test
@dp.message(IsAdmin(), Command("p"))
async def cmd_test(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    await state.set_state(States.set_payment)
    await message.answer("<b>Введите ID платежа:</b>")


# Хэндлер на команду /p
@dp.message(IsAdmin(), F.text, States.set_payment)
async def cmd_p(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    p = await PaymentCRUD.create_payment(session, message.from_user.id, 10, message.text)
    if p:
        await message.answer("<b>Платёж создан в бд!</b>")
    else:
        await message.answer("<b>Платёж не создан в бд!</b>")
    await state.clear()
