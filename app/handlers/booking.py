import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import load_config
from app.database.repository import (
    get_active_services,
    get_free_slots,
    get_service_by_id,
    get_slot_by_id,
    create_booking,
)
from app.keyboards.inline import (
    services_kb,
    slots_kb,
    confirm_kb,
    back_to_menu_kb,
    main_menu_kb,
)
from app.states import BookingStates
from app.utils import format_price, format_datetime

logger = logging.getLogger(__name__)
router = Router()
config = load_config()


# ========== ШАГ 1: Показать услуги ==========

@router.callback_query(F.data == "start_booking")
async def start_booking(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    services = await get_active_services(session)

    if not services:
        await callback.message.edit_text(
            "😔 Пока нет доступных услуг.\nЗайди позже!",
            reply_markup=back_to_menu_kb(),
        )
        await callback.answer()
        return

    await state.set_state(BookingStates.choosing_service)

    await callback.message.edit_text(
        "📅 <b>Запись на услугу</b>\n\n"
        "Выбери услугу:",
        reply_markup=services_kb(services),
    )
    await callback.answer()


# ========== ШАГ 2: Выбор услуги ==========

@router.callback_query(F.data.startswith("book_service:"))
async def choose_service(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    service_id = int(callback.data.split(":")[1])
    service = await get_service_by_id(session, service_id)

    if service is None:
        await callback.answer("Услуга не найдена", show_alert=True)
        return

    await state.update_data(service_id=service_id, service_name=service.name)

    slots = await get_free_slots(session, limit=20)

    if not slots:
        await callback.message.edit_text(
            "😔 Свободных слотов пока нет.\nПопробуй позже!",
            reply_markup=back_to_menu_kb(),
        )
        await state.clear()
        await callback.answer()
        return

    await state.set_state(BookingStates.choosing_slot)

    await callback.message.edit_text(
        f"✅ Услуга: <b>{service.name}</b> ({format_price(service.price)})\n\n"
        "📅 Теперь выбери удобное время:",
        reply_markup=slots_kb(slots),
    )
    await callback.answer()


# ========== ШАГ 3: Выбор слота ==========

@router.callback_query(F.data.startswith("book_slot:"))
async def choose_slot(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    slot_id = int(callback.data.split(":")[1])
    slot = await get_slot_by_id(session, slot_id)

    if slot is None or slot.is_booked:
        await callback.answer("Этот слот уже занят", show_alert=True)
        return

    await state.update_data(slot_id=slot_id)

    data = await state.get_data()

    await state.set_state(BookingStates.confirming)

    await callback.message.edit_text(
        f"📋 <b>Проверь запись:</b>\n\n"
        f"🛍 Услуга: <b>{data['service_name']}</b>\n"
        f"📅 Дата: <b>{format_datetime(slot.datetime)}</b>\n\n"
        "Всё верно?",
        reply_markup=confirm_kb(),
    )
    await callback.answer()


# ========== ШАГ 4: Подтверждение ==========

@router.callback_query(F.data == "confirm_booking")
async def confirm_booking(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user,
    bot: Bot,
):
    data = await state.get_data()
    service_id = data.get("service_id")
    slot_id = data.get("slot_id")

    if not service_id or not slot_id:
        await callback.answer("Что-то пошло не так, начни заново", show_alert=True)
        await state.clear()
        return

    try:
        booking = await create_booking(
            session=session,
            user_id=user.id,
            service_id=service_id,
            slot_id=slot_id,
            status="pending",
        )
    except ValueError as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)
        await state.clear()
        return
    except Exception as e:
        logger.exception(f"Неожиданная ошибка при создании записи: {e}")
        await callback.answer("Что-то пошло не так, попробуй позже", show_alert=True)
        await state.clear()
        return

    slot = await get_slot_by_id(session, slot_id)

    await callback.message.edit_text(
        f"🎉 <b>Запись создана!</b>\n\n"
        f"Номер: <b>#{booking.id}</b>\n"
        f"🛍 Услуга: <b>{data['service_name']}</b>\n"
        f"📅 Дата: <b>{format_datetime(slot.datetime)}</b>\n\n"
        "Администратор свяжется с тобой для подтверждения.\n"
        "Ждём тебя! 💫",
        reply_markup=back_to_menu_kb(),
    )

    # Уведомление админу
    try:
        await bot.send_message(
            chat_id=config.admin_id,
            text=(
                f"🔔 <b>Новая запись!</b>\n\n"
                f"👤 Клиент: <b>{user.full_name}</b>"
                + (f" (@{user.username})" if user.username else "")
                + f"\n🆔 ID: <code>{user.telegram_id}</code>\n\n"
                f"🛍 Услуга: <b>{data['service_name']}</b>\n"
                f"📅 Дата: <b>{format_datetime(slot.datetime)}</b>\n"
                f"📝 Запись: #{booking.id}"
            ),
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление админу: {e}")

    await state.clear()
    await callback.answer("Запись создана!")


# ========== Отмена ==========

@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: CallbackQuery, state: FSMContext, user):
    from app.config import load_config as _lc
    cfg = _lc()
    admin_flag = user.telegram_id == cfg.admin_id

    await state.clear()
    await callback.message.edit_text(
        "❌ Запись отменена.\n\nВыбери действие:",
        reply_markup=main_menu_kb(is_admin=admin_flag),
    )
    await callback.answer()