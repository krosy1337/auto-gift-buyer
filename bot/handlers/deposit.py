from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.states import DepositState
from bot.keyboards import get_payment_keyboard
from database.models import User, Payment
from database.session import async_session
from config import CURRENCY, LOGGING_CHAT_ID, DEPOSITS_THREAD_ID
from bot.utils import format_number

router = Router()


@router.callback_query(lambda c: c.data == "deposit")
async def process_deposit(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        user = await session.get(User, callback.from_user.id)
        balance = user.balance if user else 0

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="back_to_menu")

    text = (
        f"💰 <b>Ваш текущий баланс:</b> {format_number(balance)} ⭐\n\n"
        "✍️ Введите сумму пополнения в звездах (целое число):"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(DepositState.waiting_for_amount)
    await state.update_data(msg_id=callback.message.message_id)


@router.message(DepositState.waiting_for_amount)
async def process_deposit_amount_input(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите корректное положительное число.")
        return

    await state.update_data(amount=amount)
    prices = [LabeledPrice(label=CURRENCY, amount=amount)]
    await message.answer_invoice(
        title="Пополнение звёзд",
        description=f"Пополнение баланса на {amount} ⭐",
        payload="deposit",
        currency=CURRENCY,
        prices=prices,
        reply_markup=get_payment_keyboard(amount)
    )
    await state.set_state(DepositState.waiting_for_payment)


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, state: FSMContext, bot: Bot) -> None:
    charge_id = message.successful_payment.telegram_payment_charge_id
    amount = message.successful_payment.total_amount
    user_id = message.from_user.id

    async with async_session() as session:
        new_payment = Payment(
            user_id=user_id,
            telegram_payment_charge_id=charge_id,
            amount=amount,
        )
        session.add(new_payment)
        user = await session.get(User, user_id)
        user.balance += amount
        await session.commit()

    await bot.send_message(chat_id=LOGGING_CHAT_ID, message_thread_id=DEPOSITS_THREAD_ID, text=f"Пользователь @{user.username} [{user.id}] пополнил бота на {amount} ⭐")
    await message.answer(f"✅ Успешно пополнено на {amount} ⭐!")
    await state.clear()
