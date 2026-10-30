from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repository import (
    get_active_services,
    get_user_bookings,
    get_service_by_id,
    get_slot_by_id,
)
from app.keyboards.inline import back_to_menu_kb
from app.utils import format_price, format_duration, format_datetime, format_status

router = Router()


@router.callback_query(F.data == "services")
async def show_services(callback: CallbackQuery, session: AsyncSession):
    services = await get_active_services(session)

    if not services:
        await callback.message.edit_text(
            "😔 Пока нет доступных услуг.\nЗайди позже!",
            reply_markup=back_to_menu_kb(),
        )
        await callback.answer()
        return

    text = "📋 <b>Наши услуги:</b>\n\n"
    for s in services:
        text += (
            f"<b>{s.name}</b>\n"
            f"  💰 {format_price(s.price)} | ⏱ {format_duration(s.duration_minutes)}\n\n"
        )

    text += "💡 Записаться можно через «📅 Записаться» в главном меню."

    await callback.message.edit_text(
        text,
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "my_bookings")
async def my_bookings(callback: CallbackQuery, session: AsyncSession, user):
    bookings = await get_user_bookings(session, user.id)

    if not bookings:
        await callback.message.edit_text(
            "📅 <b>Мои записи</b>\n\n"
            "У тебя пока нет записей.\n"
            "Хочешь записаться? Нажми «📅 Записаться» в меню.",
            reply_markup=back_to_menu_kb(),
        )
        await callback.answer()
        return

    text = "📅 <b>Твои записи:</b>\n\n"
    for b in bookings:
        service = await get_service_by_id(session, b.service_id)
        slot = await get_slot_by_id(session, b.slot_id)
        service_name = service.name if service else f"Услуга #{b.service_id}"
        slot_dt = format_datetime(slot.datetime) if slot else "—"

        text += (
            f"<b>#{b.id}</b> — {format_status(b.status)}\n"
            f"  🛍 {service_name}\n"
            f"  📅 {slot_dt}\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()