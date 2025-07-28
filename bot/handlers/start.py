from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message
from database.models import User
from database.session import async_session
from bot.keyboards import get_main_menu
from config import LOGGING_CHAT_ID, NEW_USERS_THREAD_ID

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message, bot: Bot) -> None:
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                balance=0,
                business_connection=None,
            )
            session.add(user)
            await bot.send_message(chat_id=LOGGING_CHAT_ID, message_thread_id=NEW_USERS_THREAD_ID,
                                   text=f"Пользователь @{message.from_user.username} [{message.from_user.id}] зарегестрировался")
            await session.commit()
        await message.answer("Добро пожаловать! Выберите действие:", reply_markup=get_main_menu())


