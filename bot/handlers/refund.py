from aiogram import Router, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import select
from database.models import Payment, Refund, User
from database.session import async_session
from config import ADMIN_USER_ID
import logging
from config import LOGGING_CHAT_ID, REFUNDS_THREAD_ID

router = Router()


def knapsack(payments, balance: int):
    n = len(payments)
    dp = [[0] * (balance + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        amount = int(payments[i - 1].amount)
        for w in range(balance + 1):
            if amount <= w:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - amount] + amount)
            else:
                dp[i][w] = dp[i - 1][w]

    # Восстановим, какие платежи были выбраны
    selected = []
    w = balance
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            payment = payments[i - 1]
            selected.append(payment)
            w -= int(payment.amount)

    return selected


async def refund_all_payments_to_user(user_id: int, bot: Bot):
    refunded_count = 0
    refunded_sum = 0.0
    try:
        async with async_session() as session:
            # Получаем все платежи пользователя
            result = await session.execute(
                select(Payment).where(Payment.user_id == user_id)
            )
            payments = result.scalars().all()

            # Получаем уже возвращённые платежи
            refunded_result = await session.execute(
                select(Refund.payment_id).where(Refund.user_id == user_id)
            )
            refunded_payment_ids = {row[0] for row in refunded_result.all()}

            # Отбираем только те, которые ещё не возвращены
            payments_to_refund = [p for p in payments if p.id not in refunded_payment_ids]

            if not payments_to_refund:
                return

            user = await session.get(User, user_id)
            if not user:
                return

            payments_to_refund = knapsack(payments_to_refund, int(user.balance))

            for payment in payments_to_refund:
                try:
                    if payment.amount > user.balance:
                        logging.info(
                            f"Пропущен возврат {payment.amount}⭐ — превышает баланс {user.balance}⭐ пользователя {user_id}")
                        continue
                    refund = await bot.refund_star_payment(
                        user_id=user_id,
                        telegram_payment_charge_id=payment.telegram_payment_charge_id
                    )
                    if refund:
                        session.add(Refund(user_id=user_id, payment_id=payment.id))
                        user.balance = max(0.0, user.balance - payment.amount)
                        refunded_count += 1
                        refunded_sum += payment.amount
                except Exception as e:
                    logging.warning(f"Не удалось вернуть платёж {payment.telegram_payment_charge_id}: {e}")
                    continue

            await session.commit()

            await bot.send_message(chat_id=LOGGING_CHAT_ID, message_thread_id=REFUNDS_THREAD_ID,
                                   text=f"🔁 Пользователю @{user.username} [{user.id}] возвращено {refunded_count} платежей на сумму {refunded_sum} ⭐")
            return [refunded_sum, refunded_count]
    except Exception as e:
        logging.error(f"[refund_all error]: {e}")


@router.message(Command("refund"))
async def command_refund_handler(message: Message, bot: Bot, command: CommandObject) -> None:
    if message.from_user.id != ADMIN_USER_ID:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    args = command.args.strip().split()
    if len(args) != 2:
        await message.answer(
            "❗ Неверный формат команды.\nПример: /refund &lt;user_id&gt; &lt;transaction_id&gt;",
            parse_mode="HTML"
        )
        return

    try:
        user_id = int(args[0])
        transaction_id = args[1]
    except ValueError:
        await message.answer("❗ Укажите коррректный user_id (целое число).")
        return

    try:
        async with async_session() as session:
            payment = await session.execute(
                select(Payment).where(Payment.user_id == user_id,
                                     Payment.telegram_payment_charge_id == transaction_id)
            )
            payment = payment.scalar_one_or_none()

            if not payment:
                await message.answer("Платёж не найден.")
                return

            refund = await bot.refund_star_payment(
                user_id=user_id,
                telegram_payment_charge_id=transaction_id
            )

            if refund:
                new_refund = Refund(user_id=user_id, payment_id=payment.id)
                session.add(new_refund)
                user = await session.get(User, user_id)
                if user:
                    user.balance = max(0.0, user.balance - payment.amount)
                await session.commit()
                await message.answer(f"Успешно возвращено {payment.amount}⭐️ пользователю {user_id}")
                await bot.send_message(chat_id=LOGGING_CHAT_ID, message_thread_id=REFUNDS_THREAD_ID,
                                       text=f"Пользователю @{user.username} [{user.id}] возвращён платёж на сумму {payment.amount} ⭐")
    except Exception as e:
        logging.error(f"[refund error]: {e}")
        await message.answer("❌ Ошибка при выполнении возврата. Убедитесь, что ID транзакции и user_id корректны.")


@router.message(Command("refund_all"))
async def command_refund_all_handler(message: Message, bot: Bot, command: CommandObject) -> None:
    if message.from_user.id != ADMIN_USER_ID:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    args = command.args.strip().split()
    if len(args) != 1:
        await message.answer("❗ Укажите только один аргумент — user_id.\nПример: /refund_all &lt;user_id&gt;")
        return

    try:
        user_id = int(args[0])
    except ValueError:
        await message.answer("❗ Некорректный user_id.")
        return
    try:
        refunded_sum, refunded_count = await refund_all_payments_to_user(user_id, bot)
        await message.answer(f"✅ Возвращено {refunded_count} платежей на сумму {refunded_sum}⭐️ пользователю {user_id}")
    except Exception as e:
        logging.error(f"[refund error]: {e}")
        await message.answer("❌ Ошибка при выполнении возврата. Убедитесь, что ID транзакции и user_id корректны.")
