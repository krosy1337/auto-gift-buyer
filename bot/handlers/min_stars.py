from aiogram import Router, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from database.session import async_session
from bot.keyboards import (
    get_min_stars_keyboard,
)
from aiogram.types import Message
from bot.handlers.autobuy import SetStarsStates, update_profile_menu
from database.models import AutobuyProfile

router = Router()


@router.callback_query(lambda c: c.data.startswith("set_min_stars_"))
async def set_min_stars_menu(callback: CallbackQuery, state: FSMContext):
    profile_id = int(callback.data.removeprefix("set_min_stars_"))
    await state.set_data({"message_id": callback.message.message_id, "profile_id": profile_id})
    await callback.message.edit_text(
        "Выберите максимальную цену подарка в звездах:",
        reply_markup=get_min_stars_keyboard(profile_id)
    )


@router.callback_query(lambda c: c.data.startswith("min_stars_"))
async def process_min_stars(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    message_id = data.get("message_id")
    profile_id = data.get("profile_id")
    data_parts = callback.data.split("_")
    if len(data_parts) < 3:
        await callback.answer("Некорректные данные.")
        return

    value = data_parts[2]

    async with async_session() as session:
        profile = await session.get(AutobuyProfile, profile_id)
        if profile and profile.user_id == callback.message.chat.id:
            profile.min_stars = None if value == "none" else int(value)
            await session.commit()

            await update_profile_menu(callback, bot, message_id, profile.id)
    await state.clear()


@router.callback_query(lambda c: c.data == "custom_min_stars")
async def ask_custom_min_stars(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    profile_id = data.get("profile_id")
    await state.set_state(SetStarsStates.min_stars)
    await state.update_data(message_id=callback.message.message_id, profile_id=profile_id)
    await callback.message.edit_text("Введите минимальную цену подарка в звездах (целое число):")


@router.message(SetStarsStates.min_stars)
async def process_custom_min_stars(message: Message, state: FSMContext, bot: Bot):
    try:
        value = int(message.text)
        if value < 0:
            raise ValueError
        data = await state.get_data()
        profile_id = data.get("profile_id")
        message_id = data.get("message_id")

        async with async_session() as session:
            profile = await session.get(AutobuyProfile, profile_id)
            if profile and profile.user_id == message.chat.id:
                profile.min_stars = value
                await session.commit()
                await message.delete()

                await update_profile_menu(message, bot, message_id, profile_id)
        await state.clear()
    except ValueError:
        await message.reply("Введите корректное положительное число.")
