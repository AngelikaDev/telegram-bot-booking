from datetime import datetime, timezone, timedelta

# Московское время (UTC+3)
MSK = timezone(timedelta(hours=3))


def now_utc() -> datetime:
    """Текущее время в UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


def now_msk() -> datetime:
    """Текущее время в Москве."""
    return datetime.now(MSK)


def format_datetime(dt: datetime) -> str:
    """Форматирует дату в '29.10.2026 14:00' (по Москве)."""
    if dt.tzinfo is None:
        # naive datetime считаем UTC
        dt = dt.replace(tzinfo=timezone.utc)
    msk_dt = dt.astimezone(MSK)
    return msk_dt.strftime("%d.%m.%Y %H:%M")


def format_price(price: int) -> str:
    """Форматирует цену: 1500 → '1 500 ₽'."""
    return f"{price:,}".replace(",", " ") + " ₽"


def format_duration(minutes: int) -> str:
    """Форматирует длительность: 90 → '1 ч 30 мин'."""
    if minutes < 60:
        return f"{minutes} мин"
    hours, mins = divmod(minutes, 60)
    if mins == 0:
        return f"{hours} ч"
    return f"{hours} ч {mins} мин"


STATUS_EMOJI = {
    "pending": "⏳",
    "confirmed": "✅",
    "cancelled": "❌",
    "done": "🏁",
}

STATUS_LABEL = {
    "pending": "Ожидает подтверждения",
    "confirmed": "Подтверждена",
    "cancelled": "Отменена",
    "done": "Выполнена",
}


def format_status(status: str) -> str:
    """Форматирует статус: 'pending' → '⏳ Ожидает подтверждения'."""
    emoji = STATUS_EMOJI.get(status, "❓")
    label = STATUS_LABEL.get(status, status)
    return f"{emoji} {label}"