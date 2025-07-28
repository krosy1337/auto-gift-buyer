from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import AutobuyProfile
from database.session import async_session
from bot.handlers.autobuy import update_profile_menu
from aiogram.exceptions import TelegramBadRequest


class ChannelStates(StatesGroup):
    input_channel = State()


router = Router()


@router.callback_query(lambda c: c.data.startswith(("add_channel_", "change_channel_")))
async def ask_for_channel_username(callback: CallbackQuery, state: FSMContext):
    profile_id = int(callback.data.split("_")[-1])
    await state.set_state(ChannelStates.input_channel)
    await state.set_data({"profile_id": profile_id, "message_id": callback.message.message_id})

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data=f"edit_profile_{profile_id}")
    await callback.message.edit_text(text="Введите username канала (например, @mychannel):",
                                     reply_markup=builder.as_markup())


@router.message(ChannelStates.input_channel)
async def process_channel_username(message: Message, state: FSMContext, bot: Bot):
    channel_username = message.text.strip()
    if not channel_username.startswith("@"):
        await message.reply("❌ Убедитесь, что вы ввели username в формате @example_channel")
        return

    try:
        chat = await bot.get_chat(channel_username)
        if chat.type != "channel":
            await message.reply("❌ Указанный объект не является каналом.")
            return
    except TelegramBadRequest:
        await message.reply("❌ Канал не найден или бот не имеет к нему доступа.")
        return

    data = await state.get_data()
    profile_id = data["profile_id"]
    message_id = data["message_id"]

    async with async_session() as session:
        profile = await session.get(AutobuyProfile, profile_id)
        if profile and profile.user_id == message.chat.id:
            profile.channel_username = channel_username
            await session.commit()

    await message.delete()
    await state.clear()
    await update_profile_menu(message, bot, message_id, profile_id)


@router.callback_query(lambda c: c.data.startswith("remove_channel_"))
async def remove_channel_handler(callback: CallbackQuery, bot: Bot):
    profile_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        profile = await session.get(AutobuyProfile, profile_id)
        if profile and profile.user_id == callback.message.chat.id:
            profile.channel_username = None
            await session.commit()

    await update_profile_menu(callback, bot, callback.message.message_id, profile_id)
