import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import load_config
from app.database.models import Service
from app.database.repository import (
    get_active_services,
    get_service_by_id,
    get_booking_by_id,
    get_slot_by_id,
)
from app.utils import format_datetime, format_status

from app.keyboards.admin_kb import (
    admin_menu_kb,
    admin_booking_actions_kb,
    admin_delete_services_kb,
    admin_back_kb,
)
from app.keyboards.inline import main_menu_kb
from app.states import AdminServiceStates

from sqlalchemy import select, func
from app.database.models import Booking

logger = logging.getLogger(__name__)
router = Router()
config = load_config()


# ========== Проверка прав ==========

def is_admin(user) -> bool:
    return user.telegram_id == config.admin_id


# ========== /admin — вход в админку ==========

@router.message(Command("admin"))
async def cmd_admin(message: Message, user):
    if not is_admin(user):
        await message.answer("⛔ У тебя нет доступа к админке.")
        return

    await message.answer(
        "👤 <b>Админ-панель</b>\n\n"
        "Выбери действие:",
        reply_markup=admin_menu_kb(),
    )


# ========== Возврат в админку ==========

@router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery, user):
    if not is_admin(user):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "👤 <b>Админ-панель</b>\n\n"
        "Выбери действие:",
        reply_markup=admin_menu_kb(),
    )
    await callback.answer()


# ========== Список всех записей ==========

@router.callback_query(F.data == "admin_bookings")
async def admin_bookings(callback: CallbackQuery, session: AsyncSession, user):
    if not is_admin(user):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    result = await session.execute(
        select(Booking).order_by(Booking.created_at.desc()).limit(10)
    )
    bookings = result.scalars().all()

    if not bookings:
        await callback.message.edit_text(
            "📋 Записей пока нет.",
            reply_markup=admin_back_kb(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📋 <b>Последние {len(bookings)} записей</b>\n\n"
        "Каждая запись — отдельным сообщением ниже ⬇️",
    )

    for b in bookings:
        service = await get_service_by_id(session, b.service_id)
        slot = await get_slot_by_id(session, b.slot_id)

        service_name = service.name if service else f"Услуга #{b.service_id}"
        slot_dt = format_datetime(slot.datetime) if slot else "—"

        # Получаем данные пользователя
        from app.database.models import User
        result_user = await session.execute(select(User).where(User.id == b.user_id))
        client = result_user.scalar_one_or_none()
        client_name = client.full_name if client else f"User #{b.user_id}"
        client_tg = f" (@{client.username})" if client and client.username else ""

        text = (
            f"<b>#{b.id}</b> — {format_status(b.status)}\n\n"
            f"👤 {client_name}{client_tg}\n"
            f"🛍 {service_name}\n"
            f"📅 {slot_dt}\n"
            f"🕐 Создана: {format_datetime(b.created_at)}"
        )

        await callback.message.answer(
            text,
            reply_markup=admin_booking_actions_kb(b.id),
        )

    await callback.answer()


# ========== Подтвердить запись ==========

@router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm(callback: CallbackQuery, session: AsyncSession, user):
    if not is_admin(user):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    booking_id = int(callback.data.split(":")[1])
    booking = await get_booking_by_id(session, booking_id)

    if booking is None:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    if booking.status != "pending":
        await callback.answer(f"Запись уже в статусе {booking.status}", show_alert=True)
        return

    booking.status = "confirmed"
    await session.commit()

    await callback.message.edit_text(
        f"✅ Запись <b>#{booking_id}</b> подтверждена.",
        reply_markup=admin_back_kb(),
    )
    await callback.answer("Подтверждено")


# ========== Отменить запись (освободить слот) ==========

@router.callback_query(F.data.startswith("admin_cancel:"))
async def admin_cancel(callback: CallbackQuery, session: AsyncSession, user):
    if not is_admin(user):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    booking_id = int(callback.data.split(":")[1])
    booking = await get_booking_by_id(session, booking_id)

    if booking is None:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    if booking.status in ("cancelled", "done"):
        await callback.answer(f"Запись уже в статусе {booking.status}", show_alert=True)
        return

    # Освобождаем слот
    from app.database.models import Slot
    result = await session.execute(select(Slot).where(Slot.id == booking.slot_id))
    slot = result.scalar_one_or_none()
    if slot is not None:
        slot.is_booked = False

    booking.status = "cancelled"
    await session.commit()

    await callback.message.edit_text(
        f"❌ Запись <b>#{booking_id}</b> отменена, слот освобождён.",
        reply_markup=admin_back_kb(),
    )
    await callback.answer("Отменено")


# ========== Статистика ==========

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery, session: AsyncSession, user):
    if not is_admin(user):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    result = await session.execute(select(func.count(Booking.id)))
    total = result.scalar_one()

    result = await session.execute(
        select(func.count(Booking.id)).where(Booking.status == "pending")
    )
    pending = result.scalar_one()

    result = await session.execute(
        select(func.count(Booking.id)).where(Booking.status == "confirmed")
    )
    confirmed = result.scalar_one()

    result = await session.execute(select(func.count(Service.id)).where(Service.is_active == True))
    active_services = result.scalar_one()

    await callback.message.edit_text(
        "📊 <b>Статистика</b>\n\n"
        f"Всего записей: <b>{total}</b>\n"
        f"⏳ В ожидании: <b>{pending}</b>\n"
        f"✅ Подтверждено: <b>{confirmed}</b>\n\n"
        f"Активных услуг: <b>{active_services}</b>",
        reply_markup=admin_back_kb(),
    )
    await callback.answer()


# ========== Добавить услугу (FSM) ==========

@router.callback_query(F.data == "admin_add_service")
async def admin_add_service_start(callback: CallbackQuery, state: FSMContext, user):
    if not is_admin(user):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    await state.set_state(AdminServiceStates.name)
    await callback.message.edit_text(
        "➕ <b>Добавление услуги</b>\n\n"
        "Шаг 1/3: Введи <b>название</b> услуги.\n"
        "Например: <code>Стрижка мужская</code>",
        reply_markup=admin_back_kb(),
    )
    await callback.answer()


@router.message(AdminServiceStates.name)
async def admin_add_service_name(message: Message, state: FSMContext, user):
    if not is_admin(user):
        return

    name = message.text.strip()
    if len(name) < 2 or len(name) > 100:
        await message.answer("Название должно быть от 2 до 100 символов. Попробуй снова.")
        return

    await state.update_data(name=name)
    await state.set_state(AdminServiceStates.price)

    await message.answer(
        f"✅ Название: <b>{name}</b>\n\n"
        "Шаг 2/3: Введи <b>цену в рублях</b> (только число).\n"
        "Например: <code>1500</code>",
    )


@router.message(AdminServiceStates.price)
async def admin_add_service_price(message: Message, state: FSMContext, user):
    if not is_admin(user):
        return

    if not message.text.strip().isdigit():
        await message.answer("Цена должна быть числом. Попробуй снова.")
        return

    price = int(message.text.strip())
    if price < 0 or price > 1_000_000:
        await message.answer("Цена от 0 до 1 000 000. Попробуй снова.")
        return

    await state.update_data(price=price)
    await state.set_state(AdminServiceStates.duration)

    await message.answer(
        f"✅ Цена: <b>{price}₽</b>\n\n"
        "Шаг 3/3: Введи <b>длительность в минутах</b>.\n"
        "Например: <code>60</code>",
    )


@router.message(AdminServiceStates.duration)
async def admin_add_service_duration(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user,
):
    if not is_admin(user):
        return

    if not message.text.strip().isdigit():
        await message.answer("Длительность должна быть числом. Попробуй снова.")
        return

    duration = int(message.text.strip())
    if duration < 5 or duration > 600:
        await message.answer("Длительность от 5 до 600 минут. Попробуй снова.")
        return

    data = await state.get_data()

    service = Service(
        name=data["name"],
        price=data["price"],
        duration_minutes=duration,
    )
    session.add(service)
    await session.commit()

    await state.clear()
    await message.answer(
        f"🎉 <b>Услуга добавлена!</b>\n\n"
        f"Название: <b>{data['name']}</b>\n"
        f"Цена: <b>{data['price']}₽</b>\n"
        f"Длительность: <b>{duration} мин</b>",
        reply_markup=admin_back_kb(),
    )


# ========== Удалить услугу ==========

@router.callback_query(F.data == "admin_del_service")
async def admin_del_service_list(callback: CallbackQuery, session: AsyncSession, user):
    if not is_admin(user):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    services = await get_active_services(session)

    if not services:
        await callback.message.edit_text(
            "Услуг нет.",
            reply_markup=admin_back_kb(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "🗑 <b>Удаление услуг</b>\n\n"
        "Выбери услугу для скрытия (перестанет показываться клиентам):",
        reply_markup=admin_delete_services_kb(services),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_del_service_id:"))
async def admin_del_service_confirm(callback: CallbackQuery, session: AsyncSession, user):
    if not is_admin(user):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    service_id = int(callback.data.split(":")[1])
    service = await get_service_by_id(session, service_id)

    if service is None:
        await callback.answer("Услуга не найдена", show_alert=True)
        return

    service.is_active = False
    await session.commit()

    await callback.message.edit_text(
        f"🗑 Услуга <b>{service.name}</b> скрыта.",
        reply_markup=admin_back_kb(),
    )
    await callback.answer("Удалено")