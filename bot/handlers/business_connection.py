from aiogram import Router, Bot
from aiogram.types import BusinessConnection
from database.session import async_session
from database.models import User

router = Router()


@router.business_connection()
async def on_business_connection(connection: BusinessConnection, bot: Bot):
    async with async_session() as session:
        user = await session.get(User, connection.user.id)
        if user:
            if connection.is_enabled:
                is_rights_enabled = connection.rights.can_view_gifts_and_stars and connection.rights.can_transfer_and_upgrade_gifts and connection.rights.can_transfer_stars
                user.business_connection = connection.id
                text = f"✅ Установлено бизнес-подключение"
                if not is_rights_enabled:
                    text += f"\nДля корректной работы необходимо разрешить боту просмотр подарков и звёзд, отправку звёзд и отправку и улучшение подарков"
            else:
                user.business_connection = None
                text = f"❌ Разорвано бизнес-подключение"
            await session.commit()
            await bot.send_message(connection.user_chat_id, text)
