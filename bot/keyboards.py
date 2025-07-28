from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.utils import format_number


def get_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Пополнить баланс", callback_data="deposit")
    builder.button(text="⚙️ Настройка автопокупки", callback_data="settings")
    builder.button(text="🛍️ Каталог", callback_data="catalog_page_0")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_payment_keyboard(amount: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Депнуть {amount} ⭐", pay=True)
    builder.button(text="🔙 Отмена", callback_data="back_to_menu")
    return builder.as_markup()


def get_autobuy_settings_keyboard(profile_id: int, enabled: bool, channel: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Отключить" if enabled else "🚀 Включить",
        callback_data=f"toggle_profile_{profile_id}"
    )
    builder.button(text="🔽 Мин. цена", callback_data=f"set_min_stars_{profile_id}")
    builder.button(text="🔼 Макс. цена", callback_data=f"set_max_stars_{profile_id}")
    builder.button(text="📦 Лимит саплая", callback_data=f"set_supply_limit_{profile_id}")
    builder.button(text="🔁 Циклы", callback_data=f"set_purchase_cycles_{profile_id}")
    if channel:
        builder.button(text="✏ Изменить канал", callback_data=f"change_channel_{profile_id}")
        builder.button(text="❌ Отключить канал", callback_data=f"remove_channel_{profile_id}")
    else:
        builder.button(text="📡 Подключить канал", callback_data=f"add_channel_{profile_id}")
    builder.button(text="⬅️ Назад", callback_data="settings")

    channel_row = 2 if channel else 1

    builder.adjust(1, 2, 1, 1, channel_row, 1)
    return builder.as_markup()


def get_min_stars_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    values = [15, 25, 50, 100, 200, 500, 1000, 1500, 2000, 2500, 3000, 5000, 10000, 20000]
    for value in values:
        builder.button(text=format_number(value), callback_data=f"min_stars_{value}")

    builder.button(text="✍ Ввести своё", callback_data=f"custom_min_stars")
    builder.button(text="❌ Убрать лимит", callback_data=f"min_stars_none")
    builder.button(text="⬅️ Назад", callback_data=f"edit_profile_{profile_id}")
    builder.adjust(3, 3, 3, 3, 2, 1, 1)
    return builder.as_markup()


def get_max_stars_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    values = [15, 25, 50, 100, 200, 500, 1000, 1500, 2000, 2500, 3000, 5000, 7500, 10000, 15000, 20000]

    for value in values:
        builder.button(text=format_number(value), callback_data=f"max_stars_{value}")

    builder.button(text="✍ Ввести своё", callback_data=f"custom_max_stars")
    builder.button(text="❌ Убрать лимит", callback_data=f"max_stars_none")
    builder.button(text="⬅️ Назад", callback_data=f"edit_profile_{profile_id}")

    builder.adjust(3, 3, 3, 3, 3, 1, 1, 1)
    return builder.as_markup()


def get_supply_limit_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    values = [500, 1000, 1500, 2000, 3000, 5000, 7500, 10000, 15000, 25000, 50000, 100000, 250000]
    for value in values:
        builder.button(text=format_number(value), callback_data=f"supply_limit_{value}")
    builder.button(text="✍ Ввести своё", callback_data="custom_supply_limit")
    builder.button(text="❌ Убрать лимит", callback_data="supply_limit_none")
    builder.button(text="⬅️ Назад", callback_data=f"edit_profile_{profile_id}")
    builder.adjust(3, 3, 3, 2, 2, 1, 1, 1)
    return builder.as_markup()


def get_purchase_cycles_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    values = [1, 2, 3, 5, 10, 20, 30, 50, 75, 100]
    for value in values:
        builder.button(text=format_number(value), callback_data=f"purchase_cycles_{value}")
    builder.button(text="✍ Ввести своё", callback_data="custom_purchase_cycles")
    builder.button(text="⬅️ Назад", callback_data=f"edit_profile_{profile_id}")
    builder.adjust(3, 3, 3, 1, 1)
    return builder.as_markup()


def get_catalog_menu(catalog: list, page: int = 0) -> InlineKeyboardMarkup:
    ITEMS_PER_PAGE = 10
    builder = InlineKeyboardBuilder()

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_items = catalog[start:end]

    for item in current_items:
        button_text = f"{item.sticker.emoji} - {format_number(item.star_count)} ⭐"
        if item.total_count:
            button_text += f" ({format_number(item.remaining_count)}/{format_number(item.total_count)})"
        callback_data = f"catalog_collection_{item.id}"
        builder.button(text=button_text, callback_data=callback_data)

    pagination_buttons = []
    if page > 0:
        pagination_buttons.append({
            "text": "◀️",
            "callback_data": f"catalog_page_{page - 1}"
        })
    if end < len(catalog):
        pagination_buttons.append({
            "text": "▶️",
            "callback_data": f"catalog_page_{page + 1}"
        })
    for btn in pagination_buttons:
        builder.button(text=btn["text"], callback_data=btn["callback_data"])

    builder.button(text="⬅️ Назад", callback_data="back_to_menu")

    layout_scheme = [1] * len(current_items)
    if pagination_buttons:
        layout_scheme.append(len(pagination_buttons))
    layout_scheme.append(1)

    return builder.adjust(*layout_scheme).as_markup()


def get_buy_from_catalog_keyboard(collection_id) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Купить", callback_data=f"buy_collection_{collection_id}")
    builder.button(text="⬅️ Назад", callback_data="catalog_page_0")
    return builder.adjust(1, 1).as_markup()


def get_autobuy_profiles_keyboard(profiles: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, profile in enumerate(profiles, start=1):
        label = f"Профиль #{i} — {'🟢 Вкл' if profile.enabled else '🔴 Выкл'}"
        builder.button(text=label, callback_data=f"edit_profile_{profile.id}")
    builder.button(text="➕ Новый профиль", callback_data="create_profile")
    builder.button(text="⬅️ Назад", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()
