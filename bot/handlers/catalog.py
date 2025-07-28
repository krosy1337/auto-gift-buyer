from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery
from database.models import User, GiftPurchase
from database.session import async_session
from bot.keyboards import (
    get_catalog_menu,
    get_buy_from_catalog_keyboard
)
from sqlalchemy import select

router = Router()


async def update_catalog_menu(callback: CallbackQuery, bot: Bot, message_id: int, page):
    unsorted_collections = list(await bot.get_available_gifts())[0][1]
    text = (
        f"⚙️ <b>Выберите подарок из каталога</b>"
    )
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=message_id,
        text=text,
        reply_markup=get_catalog_menu(unsorted_collections, page),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("catalog_page_"))
async def handle_catalog_menu(callback: CallbackQuery):
    async with async_session() as session:
        user = await session.get(User, callback.message.chat.id)
        if not user:
            await callback.message.edit_text("❌ Вы не зарегистрированы.")
            return
    page = int(callback.data.split("_")[-1])
    await update_catalog_menu(callback, callback.bot, callback.message.message_id, page)


@router.callback_query(F.data.startswith("catalog_collection_"))
async def handle_catalog_collection(callback: CallbackQuery):
    product_id = str(callback.data.split("_")[-1])
    collection = list(filter(lambda x: x.id == product_id, list(await callback.bot.get_available_gifts())[0][1]))[0]
    text = (
        f"Подарок: {collection.sticker.emoji}\n"
        f"Стоимость: {collection.star_count} ⭐\n"
    )
    await callback.bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=get_buy_from_catalog_keyboard(product_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("buy_collection_"))
async def handle_buy(callback: CallbackQuery):
    collection_id = str(callback.data.split("_")[-1])
    collection = list(filter(lambda x: x.id == collection_id, list(await callback.bot.get_available_gifts())[0][1]))[0]
    user_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("Пользователь не найден.", show_alert=True)
            return

        if user.balance >= collection.star_count:
            success = await callback.bot.send_gift(gift_id=collection.id, chat_id=user.id)
            if success:
                user.balance -= collection.star_count
                purchase = GiftPurchase(
                    user_id=user.id,
                    collection_id=collection.id,
                    gift_star_cost=collection.star_count
                )
                session.add(purchase)
                await session.commit()
            await callback.answer()
        else:
            await callback.answer("Недостаточно средств 💸", show_alert=True)