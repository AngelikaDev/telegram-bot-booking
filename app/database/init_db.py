from datetime import timedelta

from sqlalchemy import select

from app.database.engine import engine, async_session
from app.database.models import Base, Service, Slot


async def init_database():
    """Создаёт таблицы, услуги и слоты (если их нет/мало)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # ---- УСЛУГИ ----
        result = await session.execute(select(Service))
        if result.scalars().first() is None:
            services = [
                Service(name="Стрижка женская", price=1500, duration_minutes=60),
                Service(name="Маникюр", price=2000, duration_minutes=90),
                Service(name="Педикюр", price=2500, duration_minutes=90),
            ]
            session.add_all(services)
            await session.commit()
            print(f"✅ Создано услуг: {len(services)}")

        # ---- СЛОТЫ ----
        from app.utils import now_utc
        now = now_utc()
        result = await session.execute(
            select(Slot).where(Slot.is_booked == False, Slot.datetime > now)
        )
        future_free = len(result.scalars().all())
        print(f"Свободных слотов в будущем: {future_free}")

        if future_free < 10:
            base = now.replace(hour=0, minute=0, second=0, microsecond=0)
            added = 0
            for day_offset in range(1, 8):
                for hour in (10, 12, 14, 16, 18):
                    dt = base + timedelta(days=day_offset, hours=hour)
                    result = await session.execute(
                        select(Slot).where(Slot.datetime == dt)
                    )
                    if result.scalar_one_or_none() is None:
                        session.add(Slot(datetime=dt))
                        added += 1
            await session.commit()
            print(f"✅ Добавлено слотов: {added}")
        else:
            print("ℹ️ Слотов достаточно")


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_database())