# handlers/payments.py
from typing import List, Callable, Coroutine, Any, Dict
import math
import asyncio

from aiogram.filters.command import Command
from aiogram.filters import or_f
from aiogram import Bot, F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from lang.translator import LocalizedTranslator
from db.crud import PaymentCRUD, UserCRUD

from config import dp, bot, admin_ids, admin_ids_str, base_dir
from filters.base import IsAdmin, IsAuth
from utils.telegram import send_message_admin

router = Router()


class States(StatesGroup):
    send_stars = State()
    confirm_stars = State()
    send_stars_pro = State()
    confirm_stars_pro = State()
    wait_refund = State()


# ------------------------------------- balance --------------------------------------- #


# Хэндлер на команду /balance
@router.message(or_f(Command("balance"), Command("start", magic=F.args.in_('balance'))))
async def cmd_balance(message: Message, state: FSMContext, translator: LocalizedTranslator, session) -> None:
    # Проверка регистрации
    user = await UserCRUD.get_user_by_user_id(session, str(message.from_user.id))
    if user:
        pro = 'Pro' if user.pro is True else 'Free' if user.pro is False else 'None'
        await message.answer(translator.get('balance_message', balance=user.balance, pro=pro))
    else:
        await message.answer(translator.get('not_user_message'))


# ----------------------------------- add_balance ------------------------------------- #


# Хэндлер на команду /add_balance
@router.message(IsAuth(), or_f(Command("add_balance"), Command("start", magic=F.args.in_('add_balance'))))
async def cmd_add_balance(message: Message, state: FSMContext, translator: LocalizedTranslator, session) -> None:
    await state.set_state(States.send_stars)
    await message.answer(translator.get('cmd_add_balance_message'))


# кнопка для проведения доната
@router.message(F.text, F.text.regexp(r'^[0-9]+$'), States.send_stars)
async def create_xtr_link_handler(
    message: Message, state: FSMContext, translator: LocalizedTranslator, session
) -> None:
    amount = int(message.text)
    if 10000 < amount < 0:
        await message.answer(translator.get('new_invoice_message_text_err'))
        return

    amount_stars: int = math.ceil(amount * 1)

    if message.from_user.id in admin_ids:
        amount_stars = 1

    prices: List[LabeledPrice] = [
        LabeledPrice(label="XTR", amount=amount_stars)]

    builder = InlineKeyboardBuilder()
    builder.button(text=translator.get(
        'new_invoice_btn_text', amount=amount
    ), pay=True)
    payment_keyboard = builder.as_markup()

    msg = await message.answer_invoice(
        title=translator.get('new_invoice_title', amount=amount),
        description=translator.get('new_invoice_description', amount=amount),
        prices=prices,
        provider_token="",
        payload=f"sendstars_{message.from_user.id}",
        currency="XTR",
        reply_markup=payment_keyboard,
        message_effect_id='5046509860389126442'
    )
    await state.set_state(States.confirm_stars)
    await state.update_data(message_id=msg.message_id)


# -------------------------------------- pro ------------------------------------------ #


# Хэндлер на команду /pro
@router.message(IsAuth(), or_f(Command("pro"), Command("start", magic=F.args.in_('pro'))))
async def cmd_pro(message: Message, state: FSMContext, translator: LocalizedTranslator, session) -> None:
    user_id = message.from_user.id

    # Цена за pro статус
    amount: int = 100
    amount_stars = 1 if message.from_user.id in admin_ids else amount

    # Чтение данных пользователя
    user = await UserCRUD.get_user_by_user_id(session, str(user_id))
    if not user:
        # Если пользователя нет в БД
        await message.answer(translator.get('not_user_message'))
        return

    # return await send_message_admin(str(user_id))
    # return await send_message_admin(str(user.charge_id))
    if user.pro:
        # Если у пользователя статус PRO
        if user.charge_id:
            # Если есть charge_id, показать кнопки для отмены подписки
            buttons = [
                [
                    InlineKeyboardButton(text=translator.get(
                        "cancel_pro_btn"), callback_data=f"cancel_pro")
                ],
                [
                    InlineKeyboardButton(text=translator.get(
                        "close_btn"), callback_data="close")
                ]
            ]
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer(translator.get('pro_status_already'), reply_markup=keyboard)
        else:
            # Если нет charge_id, это не должно происходить, но предусмотрим обработку
            await message.answer(translator.get('error_pro_no_charge_id'))
        return

    # Если статус PRO отсутствует
    if user.charge_id:
        # Если есть charge_id, предложить восстановление подписки
        buttons = [
            [
                InlineKeyboardButton(text=translator.get(
                    "restart_pro_btn"), callback_data=f"restart_pro")
            ],
            [
                InlineKeyboardButton(text=translator.get(
                    "close_btn"), callback_data="close")
            ]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(translator.get('pro_status_inactive'), reply_markup=keyboard)
        return

    # Если пользователь никогда не оформлял подписку
    prices: List[LabeledPrice] = [
        LabeledPrice(label="XTR", amount=amount_stars)
    ]
    try:
        # Создание ссылки на оплату
        link = await bot.create_invoice_link(
            title=translator.get('status_pro_title'),
            description=translator.get(
                'status_pro_description', amount=amount
            ),
            payload=f"pro_{user_id}",
            currency="XTR",
            prices=prices,
            provider_token="",
            subscription_period=2592000,  # 30 дней
            request_timeout=60*15,  # 15 минут
        )
        # Кнопка для оплаты
        builder = InlineKeyboardBuilder()
        builder.button(text=translator.get(
            'status_pro_btn_text', amount=amount
        ), url=link)
        payment_keyboard = builder.as_markup()

        # Отправка сообщения с ссылкой на оплату
        msg = await message.answer(
            translator.get('status_pro_description', amount=amount),
            reply_markup=payment_keyboard
        )
        await state.set_state(States.confirm_stars_pro)
        await state.update_data(message_id=msg.message_id)
    except Exception as e:
        # Если возникла ошибка при создании инвойса
        await message.answer(translator.get('payment_creation_error'))
        await send_message_admin(f'Ошибка при создании инвойса: <i>{e}</i>')


# отработка пагинации с выбором категории
@router.callback_query(F.data.in_(['restart_pro', 'cancel_pro']))
async def create_book_pagination(call: CallbackQuery, state: FSMContext, translator: LocalizedTranslator, session):
    # Цена за pro статус
    amount: int = 100
    amount_stars = 1 if call.from_user.id in admin_ids else amount

    # удалить кнопки
    await call.message.edit_reply_markup(reply_markup=None)
    # колбек в кнопке
    call_data = call.data
    user_id = str(call.from_user.id)
    # читаем пользователя
    user = await UserCRUD.get_user_by_user_id(session, user_id)
    if not user:
        await call.message.answer(translator.get('not_user_message'))
        return

    # если возобновление подписки
    is_canceled = False if call_data == 'restart_pro' else True
    status = True if call_data == 'restart_pro' else False
    try:
        # обновление подписки
        res = await bot.edit_user_star_subscription(user_id, user.charge_id, is_canceled=is_canceled)
        await UserCRUD.update_status(session, user_id, status, charge_id=user.charge_id)
        await call.answer(translator.get(f'{call_data}_success'))
        await call.message.answer(translator.get(f'{call_data}_success'))

    except Exception as e:
        print('----', e, '----', sep='\n')

        if e.message in (
            'Bad Request: SUBSCRIPTION_NOT_MODIFIED',
            'Bad Request: SUBSCRIPTION_NOT_ACTIVE'
        ):

            if e.message == 'Bad Request: SUBSCRIPTION_NOT_MODIFIED':
                await call.answer(translator.get('subscription_not_modified'))
                await call.message.answer(translator.get('subscription_not_modified'))
            elif e.message == 'Bad Request: SUBSCRIPTION_NOT_ACTIVE':
                await call.answer(translator.get('subscription_not_active_err'))
                await call.message.answer(translator.get('subscription_not_active_err'))

            # очистка статуса
            await UserCRUD.update_status(session, user_id, is_canceled)

            # Если пользователь никогда не оформлял подписку
            prices: List[LabeledPrice] = [
                LabeledPrice(label="XTR", amount=amount_stars)
            ]
            try:
                # Создание ссылки на оплату
                link = await bot.create_invoice_link(
                    title=translator.get('status_pro_title'),
                    description=translator.get(
                        'status_pro_description', amount=amount
                    ),
                    payload=f"pro_{user_id}",
                    currency="XTR",
                    prices=prices,
                    provider_token="",
                    subscription_period=2592000,  # 30 дней
                    request_timeout=60*15,  # 15 минут
                )
                # Кнопка для оплаты
                builder = InlineKeyboardBuilder()
                builder.button(text=translator.get(
                    'status_pro_btn_text', amount=amount
                ), url=link)
                payment_keyboard = builder.as_markup()

                # Отправка сообщения с ссылкой на оплату
                msg = await call.message.answer(
                    translator.get('status_pro_description', amount=amount),
                    reply_markup=payment_keyboard
                )
                await state.set_state(States.confirm_stars_pro)
                await state.update_data(message_id=msg.message_id)
            except Exception as e:
                # Если возникла ошибка при создании инвойса
                await call.message.answer(translator.get('payment_creation_error'))
                await send_message_admin(f'Ошибка при создании инвойса: <i>{e}</i>')

        else:
            await call.answer()
            await send_message_admin(e.message)

# ------------------------------------- refund ---------------------------------------- #


# Хэндлер на команду /refund
@router.message(IsAdmin(), or_f(Command("refund"), Command("start", magic=F.args.in_('refund'))))
async def cmd_refund(message: Message, state: FSMContext, translator: LocalizedTranslator, session) -> None:
    await state.set_state(States.wait_refund)
    await message.answer("<b>Введите ID транзакции для возврата средств!</b>")


# Хэндлер на возврат звёзд через админа
@router.message(IsAdmin(), F.text, ~F.text.startswith('/'), States.wait_refund)
async def refunding_proccess_handler(message: Message, state: FSMContext, translator: LocalizedTranslator, session) -> None:
    charge_id = message.text

    payment = await PaymentCRUD.get_payment_by_charge_id(session, charge_id)
    if payment:
        user_id = payment.user_id
        try:
            # попытка вернуть средства
            await bot.refund_star_payment(user_id=user_id, telegram_payment_charge_id=charge_id)

        except TelegramBadRequest as e:
            if e.message == 'Bad Request: CHARGE_ALREADY_REFUNDED':
                await send_message_admin(f'⚠️ <b>Возврат был осуществлен ранее:\nUser ID:</b> {user_id}\n\n<b>Charge ID:</b> <i>{charge_id}</i>')
            else:
                print(f'⚠️ Ошибка возврата - {e.message}')

        except Exception as e:
            print(f'⚠️ Другая ошибка - {e}')
        # очистка данных
        await state.clear()
    else:
        await message.answer(translator.get('refund_payment_none_message'))


# ------------------------------ ПОДТВЕРЖДЕНИЕ ПЛАТЕЖА --------------------------------- #

# возврат значения ок
@router.pre_checkout_query(F.invoice_payload, or_f(States.confirm_stars_pro, States.confirm_stars))
async def pre_checkout_query_handler(query: PreCheckoutQuery, translator: LocalizedTranslator, session) -> None:
    if query.invoice_payload:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message=translator.get('invoice_message_err'))


# --------------------------------- УСПЕШНЫЙ ПЛАТЁЖ ----------------------------------- #


# возврат ответа на успешную покупку и для админа с возвратом средств
@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, state: FSMContext, bot: Bot, translator: LocalizedTranslator, session) -> None:
    invoice = message.successful_payment
    payload_type, user_id = invoice.invoice_payload.split('_')
    charge_id = invoice.telegram_payment_charge_id
    amount = int(invoice.total_amount)

    user_data = await state.get_data()
    message_id = user_data.get("message_id")

    # Убираем кнопки
    await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id, reply_markup=None)

    if payload_type == 'sendstars':
        success = await PaymentCRUD.create_payment(session, user_id, amount, charge_id)
        answer_sticker = 'CAACAgEAAxkBAAIEpmd6qkT8w4kuU3yElJe283xlP-UNAAIwBAACHJgoR69A5aTn7vQGNgQ'

    elif payload_type == 'pro':
        success = await PaymentCRUD.create_payment_with_update_status(session, user_id, amount, charge_id, True, 30)
        answer_sticker = 'CAACAgEAAxkBAAII6Gd-gEk6uSGUNfdFQjbUxVdnzVseAAIDCQAC43gEAAGmNc2l6ho94jYE'

    if success:
        await message.answer_sticker(answer_sticker)

        # Чтение новых данных пользователя для отправки сообщения
        user = await UserCRUD.get_user_by_user_id(session, user_id)
        if payload_type == 'sendstars':
            await message.answer(translator.get('new_invoice_message_success', amount=amount, balance=user.balance))

        elif payload_type == 'pro':
            await message.answer(translator.get('status_pro_success'))

        # возврат для админа
        if int(user_id) in admin_ids:

            try:
                # отмена подписки
                # await bot.edit_user_star_subscription(user_id, charge_id, True)

                # попытка вернуть средства
                await bot.refund_star_payment(user_id=user_id, telegram_payment_charge_id=charge_id)

            except TelegramBadRequest as e:
                if e.message == 'Bad Request: CHARGE_ALREADY_REFUNDED':
                    await send_message_admin(f'⚠️ <b>Возврат был осуществлен ранее:\nUser ID:</b> {user_id}\n\n<b>Charge ID:</b> <i>{charge_id}</i>')
                else:
                    print(f'⚠️ Ошибка возврата - {e.message}')

            except Exception as e:
                await send_message_admin(f'⚠️ Другая ошибка - {e}')

    else:
        await message.answer(translator.get('invoice_message_err'))

    # очистка данных
    await state.clear()


# ------------------------------------- ВОЗВРАТЫ ---------------------------------------- #


# хендлер ответа на возвраты средств
@router.message(F.refunded_payment)
async def success_new_invoice_pro(message: Message, state: FSMContext, bot: Bot, translator: LocalizedTranslator, session) -> None:
    invoice = message.refunded_payment
    payload_type, user_id = invoice.invoice_payload.split('_')
    charge_id = invoice.telegram_payment_charge_id
    total_amount = invoice.total_amount

    # изменить транзакцию после возврата средств
    refunded = await PaymentCRUD.update_refunded_payment_by_charge_id(session, charge_id, True)
    if refunded:
        # обновляем статус пользователя
        if payload_type == 'pro':
            if int(user_id) not in admin_ids:
                s = await UserCRUD.update_status(session, user_id, False, 0)
                if s:
                    await bot.send_message(user_id, translator.get('cancel_pro_success'))
                else:
                    await message.answer(f'⚠️ <b>Не удалось обновить статус пользователя:\nUser ID:</b> {user_id}')
        # обновляем баланс пользователя
        elif payload_type == 'sendstars':
            if int(user_id) not in admin_ids:
                u = await UserCRUD.update_balance_down(session, user_id, total_amount)
                if u:
                    await bot.send_message(user_id, translator.get('balance_updated', amount=total_amount, balance=u.balance))
                else:
                    await message.answer(f'⚠️ <b>Не удалось обновить баланс пользователя:\nUser ID:</b> {user_id}')

        # лог если возврат не админу
        if int(user_id) not in admin_ids:
            await message.answer(f'⚠️ <b>Осуществлён возврат средств:\nUser ID:</b> {user_id}\n\n<b>Charge ID:</b> <i>{charge_id}</i>')
            await bot.send_message(user_id, translator.get('refund_stars_success', total_amount=total_amount, charge_id=charge_id))
    else:
        await message.answer(translator.get('refund_star_payment_err'))


#

# Хэндлер на возврат звёзд через админа
@router.message(IsAdmin(), F.text.startswith('/es'))
async def refunding_proccess_handler(message: Message, state: FSMContext, translator: LocalizedTranslator, session) -> None:
    charge_id = message.text.split()[1]

    try:
        # отмена подписки
        es = await bot.edit_user_star_subscription(message.from_user.id, charge_id, True)
        await message.answer(f'отменена')
    except Exception as e:
        if e == 'Telegram server says - Bad Request: SUBSCRIPTION_NOT_ACTIVE':
            await message.answer(f'⚠️ <b>Подписка не активна!</b>')
        else:
            await message.answer(f'⚠️ <b>Ошибка:</b>\n\n <i>{e}</i>')
