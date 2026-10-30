from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Все записи", callback_data="admin_bookings")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="➕ Добавить услугу", callback_data="admin_add_service")
    builder.button(text="🗑 Удалить услугу", callback_data="admin_del_service")
    builder.button(text="⬅️ В меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_booking_actions_kb(booking_id: int) -> InlineKeyboardMarkup:
    """Кнопки под конкретной записью."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить",
        callback_data=f"admin_confirm:{booking_id}",
    )
    builder.button(
        text="❌ Отменить",
        callback_data=f"admin_cancel:{booking_id}",
    )
    builder.adjust(2)
    return builder.as_markup()


def admin_delete_services_kb(services) -> InlineKeyboardMarkup:
    """Кнопки удаления услуг."""
    builder = InlineKeyboardBuilder()
    for s in services:
        builder.button(
            text=f"🗑 {s.name}",
            callback_data=f"admin_del_service_id:{s.id}",
        )
    builder.button(text="⬅️ Назад", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В админку", callback_data="admin_menu")
    return builder.as_markup()