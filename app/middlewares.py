from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.database.engine import async_session
from app.database.repository import get_or_create_user


class DatabaseMiddleware(BaseMiddleware):
    """Открывает сессию БД и подгружает пользователя в data['user']."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Определяем, от кого пришло событие
        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user

        async with async_session() as session:
            data["session"] = session
            if tg_user is not None:
                user = await get_or_create_user(
                    session=session,
                    telegram_id=tg_user.id,
                    full_name=tg_user.full_name,
                    username=tg_user.username,
                )
                data["user"] = user

            return await handler(event, data)