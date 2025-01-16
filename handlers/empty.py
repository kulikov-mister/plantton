# бот который создает книги и загружает их в Telegraph
from typing import Callable, Coroutine, Any, Dict

from aiogram.filters.command import Command
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from lang.translator import LocalizedTranslator

router = Router(name='empty_router')


# отработка кнопки отмены
@router.callback_query(F.data == "close")
async def callback_close(call: CallbackQuery, state: FSMContext, translator: LocalizedTranslator):
    await state.clear()
    await call.answer(translator.get('cancelled_message'))
    await call.message.delete_reply_markup()  # удаляем клавиатуру
    await call.message.answer(translator.get('close_message'))


# отработка команды отмены
@router.message(Command("close"))
async def message_close(message: Message, state: FSMContext, translator: LocalizedTranslator):
    await state.clear()
    await message.answer(translator.get('close_message'))


# Хэндлер на команду /start с аргументом close
@router.message(Command("start", magic=F.args != None))
async def cmd_start_args_close(message: Message, state: FSMContext, translator: LocalizedTranslator, session):
    match message.text.split()[1]:
        case "close":
            await message.answer(translator.get('close_message'))
        case "error404":
            await message.answer(translator.get('code_404'))
        # case _:
        #     await message.delete()  # удаляем сообщение
        #     await state.clear()


# пустой колбек
@router.callback_query()
async def callback_empty(call: CallbackQuery, state: FSMContext, translator: LocalizedTranslator):
    print(call.data)
    await call.answer(translator.get('callback_empty_message'))
    await call.message.delete_reply_markup()
