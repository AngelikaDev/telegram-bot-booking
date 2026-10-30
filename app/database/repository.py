from app.utils import now_utc
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, Service, Slot, Booking


# ========== USERS ==========

async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    username: Optional[str] = None,
) -> User:
    """Возвращает пользователя или создаёт нового."""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user


# ========== SERVICES ==========

async def get_active_services(session: AsyncSession) -> List[Service]:
    """Все активные услуги."""
    result = await session.execute(
        select(Service).where(Service.is_active == True).order_by(Service.id)
    )
    return list(result.scalars().all())


async def get_service_by_id(session: AsyncSession, service_id: int) -> Optional[Service]:
    result = await session.execute(
        select(Service).where(Service.id == service_id)
    )
    return result.scalar_one_or_none()


# ========== SLOTS ==========

async def get_free_slots(session: AsyncSession, limit: int = 20) -> List[Slot]:
    """Свободные слоты в будущем."""
    result = await session.execute(
        select(Slot)
        .where(Slot.is_booked == False, Slot.datetime > now_utc())
        .order_by(Slot.datetime)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_slot_by_id(session: AsyncSession, slot_id: int) -> Optional[Slot]:
    result = await session.execute(
        select(Slot).where(Slot.id == slot_id)
    )
    return result.scalar_one_or_none()


# ========== BOOKINGS ==========

async def create_booking(
    session: AsyncSession,
    user_id: int,
    service_id: int,
    slot_id: int,
    status: str = "pending",
) -> Booking:
    """Создать запись и пометить слот занятым."""
    slot = await get_slot_by_id(session, slot_id)
    if slot is None:
        raise ValueError(f"Слот {slot_id} не найден")
    if slot.is_booked:
        raise ValueError(f"Слот {slot_id} уже занят")

    booking = Booking(
        user_id=user_id,
        service_id=service_id,
        slot_id=slot_id,
        status=status,
    )
    slot.is_booked = True
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking


async def get_user_bookings(session: AsyncSession, user_id: int) -> List[Booking]:
    """Все записи пользователя."""
    result = await session.execute(
        select(Booking)
        .where(Booking.user_id == user_id)
        .order_by(Booking.created_at.desc())
    )
    return list(result.scalars().all())


async def get_booking_by_id(session: AsyncSession, booking_id: int) -> Optional[Booking]:
    result = await session.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    return result.scalar_one_or_none()