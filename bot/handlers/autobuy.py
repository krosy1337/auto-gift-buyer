from aiogram import Router, Bot
from aiogram.types import CallbackQuery, Message
from database.models import User, AutobuyProfile
from database.session import async_session
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards import (
    get_autobuy_profiles_keyboard,
    get_autobuy_settings_keyboard,
)
from sqlalchemy import select
from typing import Union
from bot.utils import format_number

router = Router()


class SetStarsStates(StatesGroup):
    min_stars = State()
    max_stars = State()
    supply_limit = State()
    purchase_cycles = State()


async def update_autobuy_menu(origin: Union[CallbackQuery, Message], bot: Bot, user: User, message_id: int):
    async with async_session() as session:
        profiles = await session.execute(
            select(AutobuyProfile).where(AutobuyProfile.user_id == user.id)
        )
        profiles = profiles.scalars().all()

    text = (
        "⚙️ <b>Профили автопокупки</b>\n\n"
        "Выберите один из профилей для настройки. "
        "Приоритет выше у того, чей номер ниже."
    )
    chat_id = origin.message.chat.id if isinstance(origin, CallbackQuery) else origin.chat.id

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=get_autobuy_profiles_keyboard(profiles)
    )


async def update_profile_menu(origin: Union[CallbackQuery, Message], bot: Bot, message_id: int, profile_id: int):
    chat_id = origin.message.chat.id if isinstance(origin, CallbackQuery) else origin.chat.id

    async with async_session() as session:
        profile = await session.get(AutobuyProfile, profile_id)

    text = (
        f"⚙️ <b>Настройки профиля</b>\n\n"
        f"Статус: {'🟢 ВКЛ' if profile.enabled else '🔴 ВЫКЛ'}\n"
        f"Мин. цена: {format_number(profile.min_stars) if profile.min_stars else '0'} ⭐\n"
        f"Макс. цена: {format_number(profile.max_stars) if profile.max_stars else '∞'} ⭐\n"
        f"Лимит саплая: {format_number(profile.supply_limit) if profile.supply_limit else '❌'}\n"
        f"Циклов: {format_number(profile.purchase_cycles)}\n"
        f"Канал: {profile.channel_username or '👤 Личный аккаунт'}"
    )

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=get_autobuy_settings_keyboard(profile.id, profile.enabled, profile.channel_username)
    )


@router.callback_query(lambda c: c.data == "settings")
async def handle_autobuy_settings(callback: CallbackQuery):
    async with async_session() as session:
        user = await session.get(User, callback.message.chat.id)
        if not user:
            await callback.message.edit_text("❌ Вы не зарегистрированы.")
            return
        await update_autobuy_menu(callback, callback.bot, user, callback.message.message_id)


@router.callback_query(lambda c: c.data.startswith("toggle_profile_"))
async def toggle_profile_handler(callback: CallbackQuery, bot: Bot):
    profile_id = int(callback.data.removeprefix("toggle_profile_"))

    async with async_session() as session:
        profile = await session.get(AutobuyProfile, profile_id)
        if not profile or profile.user_id != callback.message.chat.id:
            await callback.answer("❌ Профиль не найден.")
            return
        profile.enabled = not profile.enabled

        await session.commit()
        await update_profile_menu(callback, bot, callback.message.message_id, profile_id)


@router.callback_query(lambda c: c.data == "create_profile")
async def create_autobuy_profile(callback: CallbackQuery):
    async with async_session() as session:
        user = await session.get(User, callback.message.chat.id)
        profile = AutobuyProfile(
            user_id=user.id,
            min_stars=0,
            max_stars=None,
            supply_limit=None,
            purchase_cycles=1,
            enabled=True,
        )
        session.add(profile)
        await session.commit()
        await update_autobuy_menu(callback, callback.bot, user, callback.message.message_id)


@router.callback_query(lambda c: c.data.startswith("edit_profile_"))
async def edit_profile_handler(callback: CallbackQuery, bot: Bot):
    profile_id = int(callback.data.removeprefix("edit_profile_"))

    async with async_session() as session:
        profile = await session.get(AutobuyProfile, profile_id)
        if not profile or profile.user_id != callback.message.chat.id:
            await callback.answer("❌ Профиль не найден.")
            return

        await update_profile_menu(callback, bot, callback.message.message_id, profile_id)
