# бот который создает книги и загружает их в Telegraph
from typing import Callable, Coroutine, Any, Dict
import logging
import asyncio
import re
import os
import json

from aiogram.filters.command import Command
from aiogram import F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InlineQuery
)

from filters.base import IsAdmin, IsAuth
from middlewares.db_middleware import DatabaseMiddleware
from middlewares.technical_works import TechWorksMiddleware
from middlewares.action import ChatActionMiddleware

from lang.translator import LocalizedTranslator, Translator
from lang.localMiddleware import LangMiddleware
from utils.telegra_ph import create_book_in_telegraph
# from utils.bot_configs import set_bot_configs, set_commands
from utils.telegram import send_message_admin

from main import generate_topics_book, generate_book
from config import bot, dp
from db.crud import UserCRUD, BookCRUD, CategoryCRUD
from db.updater import sync_database
from keyboards.inline_builder import get_paginated_keyboard

af = {"chat_action": "typing"}

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)


class States(StatesGroup):
    choose_category = State()
    set_qt_topics = State()
    set_query_book = State()
    confirm_topics = State()
    confirm_chapters = State()


# ХЭНДЛЕРЫ


# Хэндлер на команду /create_book
# TODO: сделать выбор категории на разных языках
@dp.message(IsAdmin(), IsAuth(), Command("create_book"))
async def cmd_create_book(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    categories = await CategoryCRUD.get_all_categories(session)
    if not categories:
        await message.answer(translator.get('create_book_no_categories'))
        return

    await message.answer_sticker('CAACAgEAAxkBAAIB_2d1m32sj8Yk9OVZrxbO1X_-w1yrAALAAgACTVHYRii61wRcT0tBNgQ')
    await message.answer(translator.get('create_book_message'))

    kbs = [
        InlineKeyboardButton(text=cat.name, callback_data=f'cat_{cat.id}')
        for cat in categories
    ]
    keyboards = await get_paginated_keyboard(kbs, 1, "close", 'allcat', 7)
    await message.answer(translator.get('create_book_message_1'), reply_markup=keyboards)
    await state.set_state(States.choose_category)


# отработка пагинации с выбором категории
@dp.callback_query(IsAdmin(), F.data.startswith('page:'))
async def create_book_pagination(call: CallbackQuery, state: FSMContext, translator: LocalizedTranslator, session):
    _, callback, page = call.data.split(':')
    if callback == 'allcat':
        categories = await CategoryCRUD.get_all_categories(session)
        kbs = [
            InlineKeyboardButton(text=cat.name, callback_data=f'cat_{cat.id}')
            for cat in categories
        ]
        keyboards = await get_paginated_keyboard(kbs, int(page), "close", 'allcat', 7)
        await call.answer(translator.get('pagination_answer', page=page))
        await call.message.edit_reply_markup(reply_markup=keyboards)
    else:
        # пустой ответ от зацикливаний
        await call.answer()


# Хэндлер на выбор категорий и запрос количества глав
@dp.callback_query(IsAdmin(), F.data.startswith('cat_'))
async def create_book_step_1(call: CallbackQuery, state: FSMContext, translator: LocalizedTranslator):
    category = call.data.split('_')[1]
    await state.update_data(category=category)
    await call.answer(translator.get('create_book_message_2'))
    # удаляем кнопки
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(translator.get('create_book_message_2'))
    await state.set_state(States.set_qt_topics)


@dp.message(IsAdmin(), ~F.text.startswith('/'), F.text.regexp(r'^\d+$'), States.set_qt_topics)
async def create_book_step_2(message: Message, state: FSMContext, translator: LocalizedTranslator):
    qt_topics = int(message.text)
    if 1 > qt_topics > 10:
        await message.answer(translator.get('create_book_message_2_err'))
    else:
        await state.update_data(qt_topics=qt_topics)
        await message.answer(translator.get('create_book_message_3'))
        await state.set_state(States.set_query_book)


# получает название книги
# TODO: сделать потом фильтр названия, чтобы фильтр был на академическую тему
@dp.message(IsAdmin(), F.text, ~F.text.startswith('/'), States.set_query_book)
async def set_query_book(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    query_book = message.text
    user_data = await state.get_data()
    qt_topics = user_data.get('qt_topics')
    category = user_data.get('category')
    categories = await CategoryCRUD.get_all_categories(session)
    category_str = next(
        (c.name for c in categories if c.id == int(category)), None)

    msg = translator.get(
        'set_query_book', query_book=query_book,
        qt_topics=qt_topics, category_str=category_str
    )
    buttons = [
        [InlineKeyboardButton(text=translator.get(
            "next_btn"), callback_data=f"next_")],
        [InlineKeyboardButton(text=translator.get(
            "close_btn"), callback_data="close")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(msg, reply_markup=keyboard)
    await state.update_data(query_book=query_book)
    await state.set_state(States.confirm_topics)


# отработка кнопки продолжить
@dp.callback_query(IsAdmin(), F.data == "next_")
async def callback_next(call: CallbackQuery, state: FSMContext, translator: LocalizedTranslator):
    await call.answer()
    await call.message.delete_reply_markup()

    user_data = await state.get_data()
    query_book = user_data.get('query_book')
    qt_topics = user_data.get('qt_topics')

    await bot.send_chat_action(chat_id=call.message.chat.id, action='typing')

    time_sticker = 'CAACAgEAAxkBAAICAWd1m-RbRN2gp_tvTGpkayAOG0KmAAItAgACpyMhRD1AMMntg7S2NgQ'
    message = await call.message.answer_sticker(time_sticker)

    result, topics = await generate_topics_book(query_book, qt_topics)
    if not result:
        await message.answer(translator.get('generate_topics_book_error', error=topics))
        return

    if topics:
        await message.delete()  # удаляем предыдущее сообщение

        buttons = [
            [InlineKeyboardButton(text=text, callback_data=data)]
            for text, data in (
                (translator.get(
                    "next_btn"), "next_2"),
                (translator.get(
                    "next_topics_btn"), "next_"),
                (translator.get(
                    "close_btn"), "close")
            )
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await call.message.answer(
            translator.get("topics_message", topics_text='\n'.join(
                f' <b>·</b> {bt}' for bt in topics)),
            reply_markup=keyboard
        )

        await state.update_data(topics=topics)
        await state.set_state(States.confirm_chapters)
    else:
        await call.message.answer(translator.get("topics_message_error"))


# отработка кнопки подтверждения глав
@dp.callback_query(IsAdmin(), F.data == "next_2", States.confirm_chapters)
async def callback_next_2(call: CallbackQuery, state: FSMContext, translator: LocalizedTranslator, session):
    user_id = call.from_user.id
    user_name = call.from_user.username
    first_name = call.from_user.first_name
    await call.answer()
    await call.message.delete_reply_markup()

    err_sticker = 'CAACAgEAAxkBAAIFN2d7uP5FRbnXBoVAXKCGXxfGJlfSAAL-AgACgSIgRAmiojYO88U7NgQ'
    time_sticker = 'CAACAgEAAxkBAAICAWd1m-RbRN2gp_tvTGpkayAOG0KmAAItAgACpyMhRD1AMMntg7S2NgQ'
    success_sticker = 'CAACAgEAAxkBAAICM2d1plG2Fx2Dqx9YmBhXl4sJRJy3AAL6AQACjLEgRHhzeIjneBzENgQ'
    # проверка пользователя для взятия статуса
    user_status = await UserCRUD.get_user_by_user_id(session, str(call.from_user.id))
    profile_name = None
    profile_link = None
    user_data = await state.get_data()
    query_book = user_data.get('query_book')
    topics = user_data.get('topics')
    qt_topics = int(user_data.get('qt_topics'))
    category = user_data.get('category')

    if user_status and user_status.pro and user_name:
        # добавить имя пользователя если у него статус про и есть username
        profile_name = call.from_user.full_name
        profile_link = f'https://t.me/{user_name}'
    # отправка уведомления пользователю
    await call.message.answer(translator.get('start_generating_book_message'))
    message = await call.message.answer_sticker(time_sticker)
    # TODO: сделать проверку целостности книги
    # генерация книги
    full_book = await generate_book(query_book, topics)
    await message.delete()  # удаляем предыдущее сообщение
    if full_book:
        await call.message.answer(translator.get('end_generating_book_message'))
        message = await call.message.answer_sticker(time_sticker)

        # сохранение книги в файл
        books_data = json.dumps({
            'book_name': query_book,
            'books_topics': topics,
            'full_book': full_book
        }, ensure_ascii=False, indent=4)
        # создаем книгу в телеграфе
        book_url, access_token = await create_book_in_telegraph(first_name, json.loads(books_data), profile_name, profile_link)
        await message.delete()  # удаляем предыдущее сообщение
        if book_url:
            msg_book = f'📚 <b><a href="{book_url}">{query_book}</a></b>'
            price = 5 + 5*qt_topics
            # заносим в бд
            book = await BookCRUD.create_book(
                session, user_id, query_book, books_data, book_url, access_token, price, category
            )
            if not book:
                await call.message.answer_sticker(err_sticker)
                await call.message.answer(translator.get('book_create_error'))
                await send_message_admin(translator.get('book_create_error_admin', user_id=user_id, msg_book=msg_book))

            await call.message.answer(translator.get('order_create_message_ok', price=price))
            message = await call.message.answer_sticker(success_sticker)
            # отправка готовой ссылки
            await call.message.answer(msg_book)
            await state.clear()  # очистка данных пользователя

        else:
            await call.message.answer_sticker(err_sticker)
            await call.message.answer(translator.get('generating_book_message_err'))
    else:
        await call.message.answer_sticker(err_sticker)
        await call.message.answer(translator.get('generating_book_empty_message'))


# стартовые настройки бота
async def main() -> None:

    # Проверяем и обновляем структуру БД
    sync_database()

    from handlers import router
    dp.include_router(router)
    # фильтр только на сообщения внутри чата
    dp.update.filter(F.chat.type.in_({"private"}))

    # Регистрируем Middleware с передачей экземпляра Translator
    dp.update.middleware(LangMiddleware(Translator()))

    # Регистрируем Middleware отправки статуса для всех типов сразу
    dp.message.middleware(ChatActionMiddleware())
    dp.callback_query.middleware(ChatActionMiddleware())
    dp.inline_query.middleware(ChatActionMiddleware())
    dp.chosen_inline_result.middleware(ChatActionMiddleware())
    dp.pre_checkout_query.middleware(ChatActionMiddleware())
    dp.shipping_query.middleware(ChatActionMiddleware())

    # Регистрируем Middleware для проверки технических работ
    dp.update.middleware(TechWorksMiddleware())
    # Регистрируем Middleware для базы данных
    dp.update.middleware(DatabaseMiddleware())

    # Очистка накопленных сообщений перед стартом
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем поллинг
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
