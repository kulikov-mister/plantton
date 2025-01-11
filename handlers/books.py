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
from utils.code_generator import generate_random_string_async_lower
from utils.telegram import send_message_admin

router = Router()


class States(StatesGroup):
    set_category_name = State()
    confirm_topics = State()
    confirm_chapters = State()
    categories = State()


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
async def generate_error_result(translator, title_key, description_key):
    return [
        InlineQueryResultArticle(
            id="1",
            title=translator.get(title_key),
            description=translator.get(description_key),
            thumbnail_url="https://sun6-22.userapi.com/s/v1/if1/rLwx4UQ-0gPXldP0i_OLqIA4GwU6qcv9F4Nq0DxgG_gPp5goeEQtIIfLUfvAri67tAGHiqhX.jpg?size=250x250&quality=96&crop=0,0,250,250&ava=1",
            input_message_content=InputTextMessageContent(
                message_text=f"/start", parse_mode=ParseMode.HTML
            )
        )
    ]


# Хэндлер на команду /books
@router.message(IsAuth, or_f(Command("books"), Command("start", magic=F.args == 'books')))
async def cmd_categories(message: Message, state: FSMContext, translator: LocalizedTranslator, session) -> None:
    # Генерация категорий для теста
    categories = await CategoryCRUD.get_all_categories(session)
    captcha_code = await generate_random_string_async_lower()

    # Сохраняем код в состояние
    await state.update_data(code=captcha_code, message_id=message.message_id+1)
    # Устанавливаем состояние для работы с категориями
    await state.set_state(States.categories)

    # Генерация кнопок для каждой категории (передаем код капчи)
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=category.name,  # Название категории
                switch_inline_query_current_chat=f"#bs_{captcha_code}_{
                    category.code}"
            )
        )
    keyboards = builder.as_markup()
    # Отправляем сообщение с категориями
    await message.answer(translator.get('choose_category'), reply_markup=keyboards)


# инлайн режим для поиска книг с капчей
@router.inline_query(F.query.startswith('#bs_'), States.categories)
async def query_choose_books(inline_query: InlineQuery, state: FSMContext, translator: LocalizedTranslator, session) -> None:
    # Получаем данные из состояния
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
    books = await BookCRUD.get_all_books_by_category_code(session, category_code)
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
    results = [
        InlineQueryResultArticle(
            id=str(i),
            title=f'{translator.get("description_part_1")} {i}',
            description=book['title'],
            thumbnail_url=book.get(
                'image_url', "https://i.imgur.com/Dnm3RRZ.png"),
            input_message_content=InputTextMessageContent(
                message_text=f'''📚 <b><a href="{
                    book['book_url']}">{book['title']}</a></b>''',
                parse_mode='HTML'
            )
        ) for i, book in chunk_list
    ]

    # Отправка результатов с возвратом к категориям
    next_offset = str(offset + len(chunk_list)
                      ) if len(chunk_list) == 50 else ""
    await inline_query.answer(
        results, cache_time=0, is_personal=True,
        next_offset=next_offset,
        switch_pm_text=translator.get('switch_pm_text_books'),
        switch_pm_parameter="books"
    )


# TODO: добавить поиск книг по названию у авторизованного пользователя
# инлайн режим для поиска книг
@router.inline_query(F.query.startswith('all'))
async def query_search_books(inline_query: InlineQuery, state: FSMContext, translator: LocalizedTranslator, session) -> None:

    # Получаем список книг из категории
    category_code = 'xx9k23b12'  # для теста
    # категории для теста 7штук * 30 = 210 штук
    cats = await BookCRUD.get_all_books_by_category_code(session, category_code)
    cats = cats*30

    # TODO: добавить несколько картинок для логотипов книг
    offset = int(inline_query.offset) if inline_query.offset else 0
    chunk_list = await get_chunk_list_results(offset, cats)

    results = [InlineQueryResultArticle(
        id=str(i),  # Используем глобальный индекс
        title=f'{translator.get("description_part_1")} {i}',
        description=book['title'],
        thumbnail_url=book.get(
            'image_url', "https://i.imgur.com/Dnm3RRZ.png"),
        input_message_content=InputTextMessageContent(
            message_text=f'''📚 <b><a href="{
                book['book_url']}">{book['title']}</a></b>''',
            parse_mode='HTML'
        )) for i, book in chunk_list]

    # Устанавливаем next_offset только если есть еще результаты
    next_offset = str(
        offset + len(chunk_list)
    ) if len(chunk_list) == 50 else ""
    await inline_query.answer(
        results, cache_time=0, is_personal=True,
        next_offset=next_offset
    )


# TODO: добавить поиск книг пользователя у авторизованного пользователя
# инлайн режим для поиска книг
@router.inline_query(F.query.startswith('my'))
async def query_search_my_books(inline_query: InlineQuery, state: FSMContext, translator: LocalizedTranslator, session) -> None:

    # Получаем список книг из категории
    category_code = 'xx9k23b12'  # для теста
    # категории для теста 7штук * 30 = 210 штук
    cats = await BookCRUD.get_all_books_by_category_code(session, category_code)
    cats = cats*30

    # TODO: добавить несколько картинок для логотипов книг
    offset = int(inline_query.offset) if inline_query.offset else 0
    chunk_list = await get_chunk_list_results(offset, cats)

    results = [InlineQueryResultArticle(
        id=str(i),  # Используем глобальный индекс
        title=f'{translator.get("description_part_1")} {i}',
        description=book['title'],
        thumbnail_url=book.get(
            'image_url', "https://i.imgur.com/Dnm3RRZ.png"),
        input_message_content=InputTextMessageContent(
            message_text=f'''📚 <b><a href="{
                book['book_url']}">{book['title']}</a></b>''',
            parse_mode='HTML'
        )) for i, book in chunk_list]

    # Устанавливаем next_offset только если есть еще результаты
    next_offset = str(
        offset + len(chunk_list)
    ) if len(chunk_list) == 50 else ""
    await inline_query.answer(
        results, cache_time=0, is_personal=True,
        next_offset=next_offset
    )
