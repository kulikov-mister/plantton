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
from db.crud import UserCRUD, PaymentCRUD, BookCRUD, CategoryCRUD
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
        {"title": "Астрофизика 🔭", "translations": {"en": "Astrophysics 🔭"}},
        {"title": "Биоэтика 🧬⚖️", "translations": {"en": "Bioethics 🧬⚖️"}},
        {"title": "Классическая литература 📜📚",
            "translations": {"en": "Classical Literature 📜📚"}},
        {"title": "Компьютерная графика 💻🎨",
            "translations": {"en": "Computer Graphics 💻🎨"}},
        {"title": "Науки о Земле 🌎🌱", "translations": {"en": "Earth Sciences 🌎🌱"}},
        {"title": "Экономическая география 💰🌍",
            "translations": {"en": "Economic Geography 💰🌍"}},
        {"title": "Образовательная психология 🎓🧠",
            "translations": {"en": "Educational Psychology 🎓🧠"}},
        {"title": "Эпидемиология 😷", "translations": {"en": "Epidemiology 😷"}},
        {"title": "Эволюционная биология 🧬🐒", "translations": {
            "en": "Evolutionary Biology 🧬🐒"}},
        {"title": "Судебная медицина ⚕️⚖️", "translations": {
            "en": "Forensic Science ⚕️⚖️"}},
        {"title": "Историческая социология 🏛️🫂",
            "translations": {"en": "Historical Sociology 🏛️🫂"}},
        {"title": "История науки 🔬🏛️", "translations": {
            "en": "History of Science 🔬🏛️"}},
        {"title": "Международное право 🌎⚖️",
            "translations": {"en": "International Law 🌎⚖️"}},
        {"title": "Средневековая история 🏰",
            "translations": {"en": "Medieval History 🏰"}},
        {"title": "Современная история ⏱️🏛️",
            "translations": {"en": "Modern History ⏱️🏛️"}},
        {"title": "Нейробиология 🧠", "translations": {"en": "Neurobiology 🧠"}},
        {"title": "Философия науки 🤔🔬", "translations": {
            "en": "Philosophy of Science 🤔🔬"}},
        {"title": "Политическая экономия 🗳️💰",
            "translations": {"en": "Political Economy 🗳️💰"}},
        {"title": "Общественное здравоохранение 🏥",
            "translations": {"en": "Public Health 🏥"}},
        {"title": "Квантовая физика ⚛️🔬", "translations": {
            "en": "Quantum Physics ⚛️🔬"}},
        {"title": "Социальная работа 🦮", "translations": {"en": "Social Work 🦮"}},
        {"title": "Космическая биология 🚀🧬",
            "translations": {"en": "Space Biology 🚀🧬"}},
        {"title": "Спортивная медицина ⚽⚕️",
            "translations": {"en": "Sports Medicine ⚽⚕️"}},
        {"title": "Теоретическая информатика 💻🤔", "translations": {
            "en": "Theoretical Computer Science 💻🤔"}},
        {"title": "Женские исследования 🚺",
            "translations": {"en": "Women's Studies 🚺"}}
    ]
    for cat in new_cats:
        await CategoryCRUD.create_category(session, cat["title"], cat["translations"])
    # res = await CategoryCRUD.create_category(session, "test", {"en": "test"})
        await message.answer(f"<b>Категория {cat["title"]} создана в бд!</b>")
        await asyncio.sleep(0.5)


# Хэндлер на команду /test
@router.message(Command("test_book"))
async def cmd_test_book(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    name_book = "Обучение русскому языку с помощью Telegram бота в странах СНГ"
    category_id = 19
    content = await read_data_file(f"history/{name_book}.json")
    book_url = "https://telegra.ph/Obuchenie-russkomu-yazyku-s-pomoshchyu-Telegram-bota-v-stranah-SNG-12-31"
    if content:
        await BookCRUD.create_book(session, message.chat.id, name_book, json.dumps(content), book_url, access_token="", category_id=category_id)
        await message.answer(f"Книга <b>{name_book}</b> создана в бд!")
        await asyncio.sleep(0.5)
    else:
        await message.answer(f"<b>Книга {name_book} не найдена!</b>")


# Хэндлер на команду /test
@router.message(Command("p"))
async def cmd_test(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    await state.set_state(States.set_payment)
    await message.answer("<b>Введите ID платежа:</b>")


# Хэндлер на команду /p
@router.message(F.text, States.set_payment)
async def cmd_p(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    p = await PaymentCRUD.create_payment(session, message.from_user.id, 10, message.text)
    if p:
        await message.answer("<b>Платёж создан в бд!</b>")
    else:
        await message.answer("<b>Платёж не создан в бд!</b>")
    await state.clear()
