# handlers/donate.py
import re
import math
from typing import List

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import (
    Message, LabeledPrice, PreCheckoutQuery,
    KeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import admin_ids
from lang.translator import LocalizedTranslator


router: Router = Router(name='donate')


class States(StatesGroup):
    send_donate = State()
    donating = State()


# стартовый хендлер на команды donate
@router.message(Command('donate'))
async def cmd_donate(
    message: Message, state: FSMContext, translator: LocalizedTranslator
) -> None:
    await state.set_state(States.send_donate)
    await message.answer(translator.get('cmd_donate_message'))


# кнопка для проведения доната
@router.message(F.text, States.send_donate)
async def create_xtr_link_handler(
    message: Message, state: FSMContext, translator: LocalizedTranslator
) -> None:
    amount = message.text
    if not re.match(r"^[0-9]+$", amount) and 10000 >= int(amount) > 0:
        await message.answer(translator.get('donate_message_text_err'))
        return

    amount_stars: int = math.ceil(int(amount) * 1)

    if message.from_user.id in admin_ids:
        amount_stars = 1

    prices: List[LabeledPrice] = [
        LabeledPrice(label="XTR", amount=amount_stars)]

    builder = InlineKeyboardBuilder()
    builder.button(text=translator.get('donate_btn_text'), pay=True)
    payment_keyboard = builder.as_markup()

    msg = await message.answer_invoice(
        title=translator.get('donate_invoice_title'),
        description=translator.get('donate_invoice_description'),
        prices=prices,
        provider_token="",
        payload=f"donate_{message.from_user.id}",
        currency="XTR",
        reply_markup=payment_keyboard,
        message_effect_id='5044134455711629726',  # ❤️
    )
    await state.set_state(States.donating)
    await state.update_data(message_id=msg.message_id)


# возврат значения ок
@router.pre_checkout_query(States.donating)
async def success_payment_donate(pcq: PreCheckoutQuery, translator: LocalizedTranslator):
    await pcq.answer(ok=True, error_message="Что-то пошло не так, повторите попытку позже..")


# возврат ответа на успешную покупку
@router.message(F.successful_payment, States.donating)
async def success_donate_message(message: Message, state: FSMContext, bot: Bot, translator: LocalizedTranslator):
    user_data = await state.get_data()
    message_id = user_data.get("message_id")
    await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id, reply_markup=None)
    await message.answer_sticker('CAACAgEAAxkBAAICmWd113OzFCX-_QpQtrou7Rk8wJeQAALJBwAC43gEAAGESQ6JsVOaWzYE')
    await message.answer(translator.get('donate_message_success'))
    await state.clear()
