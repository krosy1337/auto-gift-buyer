import logging
from aiogram import Bot
from sqlalchemy import select

from config import LOGGING_CHAT_ID, NEW_GIFTS_THREAD_ID
from database.models import User, UserCollection, Collection, GiftPurchase, AutobuyProfile
from database.session import async_session


async def gift_monitor(bot: Bot):
    while True:
        try:
            async with async_session() as session:
                unsorted_collections = list(await bot.get_available_gifts())[0][1]
                collections = sorted(filter(lambda y: y.total_count, unsorted_collections), key=lambda x: x.star_count, reverse=True)

                processed_collections = await session.execute(select(Collection.id))
                processed_ids = set(processed_collections.scalars().all())
                text = ""
                for collection in collections:
                    if collection.id not in processed_ids:
                        text += f"id: {collection.id}, cost: {collection.star_count}\n"
                if text:
                    await bot.send_message(chat_id=LOGGING_CHAT_ID, message_thread_id=NEW_GIFTS_THREAD_ID,
                                           text=text)
                for collection in collections:
                    if collection.id in processed_ids:
                        continue
                    if collection.id not in processed_ids:
                        new_collection = Collection(id=collection.id)
                        session.add(new_collection)
                        await session.commit()
                        processed_ids.add(collection.id)
                    result = await session.execute(select(AutobuyProfile))
                    profiles = result.scalars().all()

                    all_done = False
                    while not all_done:
                        all_done = True
                        for profile in profiles:
                            if not profile.enabled:
                                continue

                            user_id = profile.user_id
                            chat_id = profile.channel_username or user_id
                            result = await session.execute(
                                select(UserCollection).where(
                                    UserCollection.user_id == user_id,
                                    UserCollection.collection_id == collection.id,
                                    UserCollection.profile_id == profile.id
                                )
                            )
                            user_collection = result.scalars().first()
                            if user_collection and user_collection.completed:
                                continue

                            if not user_collection:
                                user_collection = UserCollection(
                                    user_id=user_id,
                                    collection_id=collection.id,
                                    profile_id=profile.id,
                                    gifts_bought=0,
                                    completed=False
                                )
                                session.add(user_collection)
                                await session.commit()

                            if profile.min_stars and collection.star_count < profile.min_stars:
                                continue
                            if profile.max_stars and collection.star_count > profile.max_stars:
                                continue
                            if profile.supply_limit and collection.total_count > profile.supply_limit:
                                continue

                            if user_collection.gifts_bought >= profile.purchase_cycles:
                                user_collection.completed = True
                                await session.commit()
                                continue

                            result = await session.execute(select(User).where(User.id == user_id))
                            user = result.scalar_one_or_none()
                            if not user:
                                continue
                            if user.balance < collection.star_count:
                                user_collection.completed = True
                                await session.commit()
                                continue

                            success = await bot.send_gift(gift_id=collection.id, chat_id=chat_id)
                            if success:
                                user.balance -= collection.star_count
                                user_collection.gifts_bought += 1
                                if user_collection.gifts_bought >= profile.purchase_cycles:
                                    user_collection.completed = True

                                purchase = GiftPurchase(
                                    user_id=user_id,
                                    collection_id=collection.id,
                                    gift_star_cost=collection.star_count,
                                    profile_id=profile.id
                                )
                                session.add(purchase)
                                await session.commit()
                                logging.info(f"[monitor] Пользователь {user.id} купил подарок из {collection.id} для {chat_id}; Профиль({profile.id})")
                                all_done = False
                            else:
                                logging.error(f"[monitor] Не удалось купить подарок для пользователя {chat_id} user({user.id})")
                    await session.commit()
        except Exception as e:
            logging.error(f"[monitor error]: {e}")
