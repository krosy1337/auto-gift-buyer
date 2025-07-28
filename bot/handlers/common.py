from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from bot.keyboards import get_main_menu
import logging

router = Router()


@router.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text(
            "📍 Главное меню:",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Error editing message: {e}")
        await callback.message.answer(
            "📍 Главное меню:",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    await callback.answer()
