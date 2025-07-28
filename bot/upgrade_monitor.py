import asyncio
import logging
import math

from aiogram import Bot
from sqlalchemy import select
from database.models import User
from database.session import async_session
from aiogram.types import Gift
from aiogram.exceptions import TelegramBadRequest


def get_minimal_upgrade_price(gift: Gift):
    if gift.star_count < 500:
        return 25
    return math.floor(gift.star_count*0.2)


async def upgrade_monitor(bot: Bot):
    while True:
        try:
            async with async_session() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
                for user in users:
                    if not user.business_connection:
                        continue
                    owned_gifts = await bot.get_business_account_gifts(user.business_connection)
                    gifts = owned_gifts.gifts
                    sorted_gifts = list(filter(lambda x: x.type == "regular" and x.gift.total_count, gifts))

                    for gift in sorted_gifts:
                        if not gift.gift.upgrade_star_count:
                            continue
                        if gift.gift.upgrade_star_count <= get_minimal_upgrade_price(gift.gift):
                            if gift.prepaid_upgrade_star_count:
                                star_count = 0
                            else:
                                star_count = gift.gift.upgrade_star_count
                            try:
                                await bot.upgrade_gift(user.business_connection, gift.owned_gift_id, False,
                                                       star_count)
                            except TelegramBadRequest as e:
                                logging.warning(f"[upgrade failed] User {user.id}, gift {gift.owned_gift_id}: {e}")
        except Exception as e:
            logging.error(f"[upgrade monitor error]: {e}")
