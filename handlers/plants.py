# handlers/admin.py
from typing import List, Tuple, Any
import random
import json

from aiogram.filters.command import Command
from aiogram.filters import or_f
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, ChosenInlineResult, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder

from filters.base import IsAdmin, IsAuth
from keyboards.inline_builder import get_paginated_keyboard

from lang.translator import LocalizedTranslator
from db.crud import UserCRUD, CategoryCRUD

from config import bot, thumbnails_books, thumbnail_default
from utils.code_generator import generate_random_string_async_lower


router = Router()


class States(StatesGroup):
    set_category_name = State()
    categories = State()
    choose_category = State()
    set_qt_topics = State()
    set_query_book = State()
    confirm_topics = State()
    confirm_chapters = State()


# УТИЛИТЫ


# делит список на части возвращая кортеж индексов с элементами
async def get_chunk_list_results(start_index: int, list_arr: list, size: int = 50) -> List[Tuple[int, Any]]:
    """Делит список на части, возвращая список кортежей (индекс, элемент)."""
    overall_items = len(list_arr)
    # Если начальный индекс выходит за пределы списка, возвращаем пустой список
    if start_index >= overall_items:
        return []
    # Вычисляем конечный индекс части списка
    end_index = min(start_index + size, overall_items)
    # Возвращаем часть списка в виде кортежей (глобальный индекс, элемент)
    return [(i + 1, list_arr[i]) for i in range(start_index, end_index)]


# Утилита для создания результатов с ошибками
async def generate_error_result(translator, title_key, description_key, thumbnail_url: str = None):
    return [
        InlineQueryResultArticle(
            id="1",
            title=translator.get(title_key),
            description=translator.get(description_key),
            thumbnail_url=thumbnail_url or "https://sun6-22.userapi.com/s/v1/if1/rLwx4UQ-0gPXldP0i_OLqIA4GwU6qcv9F4Nq0DxgG_gPp5goeEQtIIfLUfvAri67tAGHiqhX.jpg?size=250x250&quality=96&crop=0,0,250,250&ava=1",
            input_message_content=InputTextMessageContent(
                message_text=f"/start", parse_mode=ParseMode.HTML
            )
        )
    ]


# ХЭНДЛЕРЫ


# Хэндлер на команду /plants
@router.message(IsAuth(check_balance=300), Command("plants"))
async def cmd_plants(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    categories = await CategoryCRUD.get_all_categories(session)
    language_code = message.from_user.language_code or 'en'
    if not categories:
        await message.answer(translator.get('create_book_no_categories'))
        return

    await message.answer_sticker('CAACAgEAAxkBAAIB_2d1m32sj8Yk9OVZrxbO1X_-w1yrAALAAgACTVHYRii61wRcT0tBNgQ')
    await message.answer(translator.get('create_book_message'))

    kbs = [
        InlineKeyboardButton(
            text=cat.translations.get(language_code, cat.name),
            callback_data=f'cat_{cat.id}'
        )
        for cat in categories
    ]
    keyboards = await get_paginated_keyboard(kbs, 1, "close", 'allcat', 10)
    await message.answer(translator.get('create_book_message_1'), reply_markup=keyboards)
    await state.set_state(States.choose_category)


# Хэндлер на выбор категорий и запрос количества ton
@router.callback_query(F.data.startswith('cat_'))
async def create_book_step_1(call: CallbackQuery, state: FSMContext, translator: LocalizedTranslator):
    category = call.data.split('_')[1]
    await state.update_data(category=category)
    await call.answer(translator.get('create_book_message_2'))
    # удаляем кнопки
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(translator.get('create_book_message_2'))
    await state.set_state(States.set_qt_topics)


# получает количество ton
@router.message(~F.text.startswith('/'), F.text.regexp(r'^\d+$'), States.set_qt_topics)
async def create_book_step_2(message: Message, state: FSMContext, translator: LocalizedTranslator):
    qt_topics = int(message.text)
    if 1 > qt_topics > 10:
        await message.answer(translator.get('create_book_message_2_err'))
    else:
        await state.update_data(qt_topics=qt_topics)
        await message.answer(translator.get('create_book_message_3'))
        await state.set_state(States.set_query_book)


# ПАГИНАЦИЯ

# отработка пагинации с выбором категории
@router.callback_query(F.data.startswith('page:'))
async def create_book_pagination(call: CallbackQuery, state: FSMContext, translator: LocalizedTranslator, session):
    language_code = call.from_user.language_code or 'en'
    _, callback, page = call.data.split(':')
    # в режиме выбора категории для создания книг
    if callback == 'allcat':
        categories = await CategoryCRUD.get_all_categories(session)
        kbs = [
            InlineKeyboardButton(
                text=category.translations.get(language_code, category.name),
                callback_data=f'cat_{category.id}')
            for category in categories
        ]
        keyboards = await get_paginated_keyboard(kbs, int(page), "close", 'allcat', 10)
        await call.answer(translator.get('pagination_answer', page=page))
        await call.message.edit_reply_markup(reply_markup=keyboards)
    # в режиме выбора категории в инлайн-режиме
    elif callback == 'inlcats':
        captcha_code = await generate_random_string_async_lower()
        await state.update_data(code=captcha_code)
        categories = await CategoryCRUD.get_all_categories(session)
        kbs = [
            InlineKeyboardButton(
                text=category.translations.get(language_code, category.name),
                switch_inline_query_current_chat=f"#bs_{captcha_code}_{category.code}")
            for category in categories
        ]
        keyboards = await get_paginated_keyboard(kbs, int(page), "close", 'inlcats', 10)
        await call.answer(translator.get('pagination_answer', page=page))
        await call.message.edit_reply_markup(reply_markup=keyboards)
    else:
        # пустой ответ от зацикливаний
        await call.answer()


# ИНЛАЙН РЕЖИМ


# Хэндлер на команду /books
@router.message(IsAuth(), or_f(Command("books"), Command("start", magic=F.args == 'books')))
async def cmd_books(message: Message, state: FSMContext, translator: LocalizedTranslator, session) -> None:
    language_code = message.from_user.language_code or 'en'
    # Генерация категорий для теста
    categories = await CategoryCRUD.get_all_categories(session)
    if not categories:
        await message.answer(translator.get('no_categories'))
        return

    captcha_code = await generate_random_string_async_lower()

    # Сохраняем код в состояние
    await state.update_data(code=captcha_code, message_id=message.message_id+1)
    # Устанавливаем состояние для работы с категориями
    await state.set_state(States.categories)

    # Генерация кнопок для каждой категории (передаем код капчи)
    kbs = [
        InlineKeyboardButton(
            text=category.translations.get(language_code, category.name),
            switch_inline_query_current_chat=f"#bs_{captcha_code}_{category.code}")
        for category in categories
    ]
    keyboards = await get_paginated_keyboard(kbs, 1, "close", 'inlcats', 10)
    # Отправляем сообщение с категориями
    await message.answer(translator.get('choose_category'), reply_markup=keyboards)


# инлайн режим для поиска растений с капчей
@router.inline_query(F.query.startswith('#p_'), States.categories)
async def query_choose_books(inline_query: InlineQuery, state: FSMContext, translator: LocalizedTranslator, session) -> None:
    # Получаем данные из состояния
    user_id = inline_query.from_user.id
    state_data = await state.get_data()
    saved_code = state_data.get('code')
    message_id = state_data.get('message_id')

    if message_id:
        # изменение сообщения после нажатия на категорию
        await bot.edit_message_text(
            chat_id=inline_query.from_user.id, message_id=message_id,
            text=translator.get('choose_book'), reply_markup=None
        )
        await state.update_data(message_id=None)

    user = await UserCRUD.get_user_by_user_id(session, user_id)
    if not user:
        results = await generate_error_result(translator, 'not_user_title', 'not_user_description')
        await inline_query.answer(
            results, is_personal=True, cache_time=0,
            switch_pm_text=translator.get('switch_pm_text_register'),
            switch_pm_parameter='start'
        )
        return

    # Парсим запрос
    query_parts = inline_query.query.split('_')
    if len(query_parts) < 3 or query_parts[0] != '#bs':
        await inline_query.answer([], cache_time=0)
        return

    _, query_code, category_code = query_parts

    # Если капча неверная
    if query_code != saved_code:
        results = await generate_error_result(translator, 'code_404', 'code_404_description')
        await inline_query.answer(
            results, is_personal=True, cache_time=0, switch_pm_text=translator.get('switch_pm_text_start'),
            switch_pm_parameter='start'
        )
        await state.update_data(code=None)
        return

    # Получаем список книг из категории
    books = None
    if not books:
        results = await generate_error_result(translator, 'no_more_results', 'no_more_results_description')
        await inline_query.answer(
            results, is_personal=True, cache_time=0, switch_pm_text=translator.get('switch_pm_text_books'),
            switch_pm_parameter="books"
        )
        await state.update_data(code=None)
        return

    # Пагинация
    offset = int(inline_query.offset) if inline_query.offset else 0
    chunk_list = await get_chunk_list_results(offset, books)

    if not chunk_list:
        # Очистка капчи на последней странице
        await state.update_data(code=None)
        return

    # Генерация результатов
    previous_thumbnail = None

    results = []
    for i, book in chunk_list:
        # Выбор случайной ссылки, которая отличается от предыдущей
        if len(thumbnails_books) > 1:
            thumbnail_url = random.choice(
                [thumb for thumb in thumbnails_books if thumb != previous_thumbnail])
        else:
            # Если в массиве только одна ссылка, использовать её
            thumbnail_url = thumbnails_books[0] if thumbnails_books else thumbnail_default

        # Обновление предыдущей ссылки
        previous_thumbnail = thumbnail_url

        # Добавление результата в список
        results.append(
            InlineQueryResultArticle(
                id=str(i),
                title=f'{translator.get("description_part_1")} {i}',
                description=book.name_book,
                thumbnail_url=thumbnail_url,
                input_message_content=InputTextMessageContent(
                    message_text=f'''📚 <b><a href="{
                        book.book_url}">{book.name_book}</a></b>''',
                    parse_mode='HTML'
                )
            )
        )

    # Отправка результатов с возвратом к категориям
    next_offset = str(offset + len(chunk_list)
                      ) if len(chunk_list) == 50 else ""
    await inline_query.answer(
        results, cache_time=0, is_personal=True,
        next_offset=next_offset,
        switch_pm_text=translator.get('switch_pm_text_books'),
        switch_pm_parameter="books"
    )


# инлайн режим для поиска книг
@router.inline_query(F.query.startswith('my'))
async def query_search_my_books(inline_query: InlineQuery, state: FSMContext, translator: LocalizedTranslator, session) -> None:
    user_id = inline_query.from_user.id
    query = inline_query.query[4:]  # фильтрация для поиска

    user = await UserCRUD.get_user_by_user_id(session, user_id)
    if not user:
        results = await generate_error_result(translator, 'not_user_title', 'not_user_description')
        await inline_query.answer(
            results, is_personal=True, cache_time=0, switch_pm_text=translator.get('switch_pm_text_start'),
            switch_pm_parameter='start')
        return

    # Получаем список книг пользователя
    books = None

    if not books:
        results = await generate_error_result(translator, 'no_more_results', 'no_more_results_description')
        await inline_query.answer(
            results, is_personal=True, cache_time=0, switch_pm_text=translator.get('switch_pm_text_books'),
            switch_pm_parameter="books"
        )
        await state.update_data(code=None)
        return

    # фильтрация книг по запросу
    filtred_books = [
        book for book in books if query.lower()
        in book.name_book.lower()
    ]

    # TODO: добавить несколько картинок для логотипов книг
    offset = int(inline_query.offset) if inline_query.offset else 0
    chunk_list = await get_chunk_list_results(offset, books)

    previous_thumbnail = None
    results = []
    for i, book in chunk_list:
        # Выбор случайной ссылки, которая отличается от предыдущей
        if len(thumbnails_books) > 1:
            thumbnail_url = random.choice(
                [thumb for thumb in thumbnails_books if thumb != previous_thumbnail])
        else:
            # Если в массиве только одна ссылка, использовать её
            thumbnail_url = thumbnails_books[0] if thumbnails_books else thumbnail_default

        # Обновление предыдущей ссылки
        previous_thumbnail = thumbnail_url

        # Добавление результата в список
        results.append(
            InlineQueryResultArticle(
                id=str(i),
                title=f'{translator.get("description_part_1")} {i}',
                description=book.name_book,
                thumbnail_url=thumbnail_url,
                input_message_content=InputTextMessageContent(
                    message_text=f'''📚 <b><a href="{
                        book.book_url}">{book.name_book}</a></b>''',
                    parse_mode='HTML'
                )
            )
        )

    # Устанавливаем next_offset только если есть еще результаты
    next_offset = str(
        offset + len(chunk_list)
    ) if len(chunk_list) == 50 else ""
    await inline_query.answer(
        results, cache_time=0, is_personal=True, next_offset=next_offset,
        switch_pm_text=translator.get('switch_pm_text_start'), switch_pm_parameter='start'
    )
