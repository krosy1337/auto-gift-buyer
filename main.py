import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from database.models import Base
from database.session import engine
from bot.handlers.start import router as start_router
from bot.handlers.deposit import router as deposit_router
from bot.handlers.autobuy import router as autobuy_router
from bot.handlers.refund import router as refund_router
from bot.handlers.common import router as common_router
from bot.handlers.catalog import router as catalog_router
from bot.handlers.min_stars import router as min_stars_router
from bot.handlers.max_stars import router as max_stars_router
from bot.handlers.supply_limit import router as supply_limit_router
from bot.handlers.purchase_cycles import router as purchase_cycles_router
from bot.handlers.channel import router as channel_router
from bot.handlers.business_connection import router as business_connection_router
from bot.gift_monitor import gift_monitor
from bot.upgrade_monitor import upgrade_monitor


async def on_startup(bot: Bot):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    asyncio.create_task(gift_monitor(bot))
    asyncio.create_task(upgrade_monitor(bot))


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(common_router)
    dp.include_router(start_router)
    dp.include_router(deposit_router)
    dp.include_router(autobuy_router)
    dp.include_router(refund_router)
    dp.include_router(catalog_router)
    dp.include_router(min_stars_router)
    dp.include_router(max_stars_router)
    dp.include_router(supply_limit_router)
    dp.include_router(purchase_cycles_router)
    dp.include_router(channel_router)
    dp.include_router(business_connection_router)

    dp.startup.register(on_startup)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
