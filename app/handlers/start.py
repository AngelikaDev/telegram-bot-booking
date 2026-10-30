from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from app.keyboards.inline import main_menu_kb, back_to_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, user):
    from app.config import load_config
    config = load_config()
    admin_flag = user.telegram_id == config.admin_id

    await message.answer(
        f"👋 Привет, {user.full_name}!\n\n"
        "Я бот для записи на услуги.\n"
        "Выбери, что тебя интересует:",
        reply_markup=main_menu_kb(is_admin=admin_flag),
    )


@router.message(Command("help"))
async def cmd_help(message: Message, user):
    from app.config import load_config
    config = load_config()

    text = (
        "ℹ️ <b>Помощь</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/help — эта справка\n"
    )

    if user.telegram_id == config.admin_id:
        text += (
            "/admin — админ-панель\n"
            "\n<b>Админ-команды:</b>\n"
            "• 📋 Все записи — управление записями\n"
            "• 📊 Статистика — сводка\n"
            "• ➕ Добавить услугу — новая услуга\n"
            "• 🗑 Удалить услугу — скрыть услугу\n"
        )

    text += (
        "\n<b>Как записаться?</b>\n"
        "1. Нажми «📅 Записаться»\n"
        "2. Выбери услугу\n"
        "3. Выбери удобное время\n"
        "4. Подтверди запись\n\n"
        "По вопросам: @твой_username"
    )

    await message.answer(text)


@router.callback_query(F.data == "main_menu")
async def back_to_menu(callback: CallbackQuery, user):
    from app.config import load_config
    config = load_config()
    admin_flag = user.telegram_id == config.admin_id

    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыбери действие:",
        reply_markup=main_menu_kb(is_admin=admin_flag),
    )
    await callback.answer()


@router.callback_query(F.data == "about")
async def about(callback: CallbackQuery):
    await callback.message.edit_text(
        "ℹ️ <b>О нас</b>\n\n"
        "Мы — студия красоты «Пример».\n"
        "📍 Адрес: ул. Примерная, 1\n"
        "🕐 Работаем: 10:00 – 20:00\n"
        "📞 Телефон: +7 (999) 123-45-67",
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()