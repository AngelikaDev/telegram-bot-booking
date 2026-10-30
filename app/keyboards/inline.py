from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models import Service, Slot


def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Записаться", callback_data="start_booking")
    builder.button(text="📋 Услуги", callback_data="services")
    builder.button(text="📅 Мои записи", callback_data="my_bookings")
    builder.button(text="ℹ️ О нас", callback_data="about")
    if is_admin:
        builder.button(text="👤 Админка", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В меню", callback_data="main_menu")
    return builder.as_markup()


def services_kb(services: list[Service]) -> InlineKeyboardMarkup:
    """Кнопки выбора услуги. callback_data = book_service:{id}"""
    builder = InlineKeyboardBuilder()
    for s in services:
        builder.button(
            text=f"{s.name} — {s.price}₽",
            callback_data=f"book_service:{s.id}",
        )
    builder.button(text="⬅️ Отмена", callback_data="cancel_booking")
    builder.adjust(1)  # каждая кнопка на новой строке
    return builder.as_markup()


def slots_kb(slots: list[Slot]) -> InlineKeyboardMarkup:
    """Кнопки выбора слота. callback_data = book_slot:{id}"""
    builder = InlineKeyboardBuilder()
    for slot in slots:
        label = slot.datetime.strftime("%d.%m %H:%M")
        builder.button(text=label, callback_data=f"book_slot:{slot.id}")
    builder.button(text="⬅️ Отмена", callback_data="cancel_booking")
    builder.adjust(2)  # по 2 слота в ряд
    return builder.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    """Подтверждение записи."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_booking")
    builder.button(text="❌ Отмена", callback_data="cancel_booking")
    builder.adjust(1)
    return builder.as_markup()