# handlers/admin.py
import asyncio
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
from db.crud import UserCRUD, BookCRUD, CategoryCRUD

from config import dp, bot, admin_ids, admin_ids_str, base_dir
from utils.telegra_ph import get_page
from utils.telegram import send_message_admin

router = Router()
# установка единых фильтров на админа
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())
# router.inline_query.filter(IsAdmin())


class States(StatesGroup):
    set_category_name = State()


# Хэндлер на команду /stats
@router.message(Command("stats"))
async def cmd_stats(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    books = await BookCRUD.get_all_books(session)
    msg = ''.join([f'{i}. {book.name_book}\n' for i, book in enumerate(books)])
    await message.answer(msg)


# Хэндлер на команду /update_views
@router.message(Command("update_views"))
async def cmd_update_views(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    books = await BookCRUD.get_all_books(session)
    # res = [await get_page(b.book_url) for b in books]

    semaphore = asyncio.Semaphore(30)

    async def get_page_sem(url):
        async with semaphore:
            return await get_page(url)

    tasks = [asyncio.create_task(get_page_sem(b.book_url)) for b in books]
    res = await asyncio.gather(*tasks)

    books_stat = ''.join(
        [f'<b>- {i}</b>. <a href="{r.get('url')}">{r.get('title')}</a> | Views: {r.get('views')}\n' for i, r in enumerate(sorted(res, key=lambda p: p.get('views'), reverse=True)[:10], start=1)])
    books_stat_msg = '<b>Топ 10 книг месяца:</b>\n\n'+books_stat
    await message.answer(books_stat_msg, disable_web_page_preview=True)
    # await bot.send_message('@app5_news', books_stat_msg, disable_web_page_preview=True)

# ----------------------------------- добавить категорию -------------------------------------- #


# Хэндлер на команду /add_category
@router.message(Command("add_category"))
async def cmd_add_category(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    await message.answer_sticker('CAACAgEAAxkBAAIB-md1m0AGoO0FAVGqn9DIXWMSozJoAAJ_AwACjrnpRxz1DWc-DE2ZNgQ')
    await message.answer('Привет! тут тестовое сообщение')
