# handlers/test.py
from typing import Callable, Coroutine, Any, Dict
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
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, URLInputFile
from aiogram.exceptions import TelegramBadRequest

from lang.translator import LocalizedTranslator
from db.crud import UserCRUD, PaymentCRUD, CategoryCRUD
from utils.telegram import send_message_admin
from utils.tools import read_data_file

from config import dp, bot, get_file_url, admin_ids, admin_ids_str, base_dir
from filters.base import IsAdmin

router = Router()
router.message.filter(IsAdmin())


class States(StatesGroup):
    set_test = State()
    set_payment = State()
    confirm_topics = State()
    confirm_chapters = State()


# отработка  тест стикеров
@router.message(F.sticker)
async def message_sticker_test(message: Message, state: FSMContext, translator: LocalizedTranslator):
    file = await bot.get_file(message.sticker.file_id)
    url = f'{get_file_url}{file.file_path}'
    await message.answer(url)
    await message.answer_animation(URLInputFile(url))


# отработка  тест фото
@router.message(F.photo)
async def message_photo_test(message: Message, state: FSMContext, translator: LocalizedTranslator):
    file = await bot.get_file(message.photo[-1].file_id)
    url = f'{get_file_url}{file.file_path}'
    await message.answer(url)


# отработка  тест видео
@router.message(F.video)
async def message_video_test(message: Message, state: FSMContext, translator: LocalizedTranslator):
    file = await bot.get_file(message.video.file_id)
    url = f'{get_file_url}{file.file_path}'
    await message.answer(url)


# Хэндлер на команду /test
@router.message(Command("test"))
async def cmd_test(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    new_cats = [
        {"title": "Астрофизика 🔭", "translations": {"en": "Astrophysics 🔭"}}
    ]
    for cat in new_cats:
        await CategoryCRUD.create_category(session, cat["title"], cat["translations"])
        await message.answer(f"<b>Категория {cat["title"]} создана в бд!</b>")
        await asyncio.sleep(0.5)
