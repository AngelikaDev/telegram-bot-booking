from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import BigInteger, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    bookings: Mapped[List["Booking"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} tg={self.telegram_id} name={self.full_name}>"


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    price: Mapped[int] = mapped_column(Integer)  # в рублях
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    bookings: Mapped[List["Booking"]] = relationship(back_populates="service")

    def __repr__(self) -> str:
        return f"<Service id={self.id} name={self.name} price={self.price}>"


class Slot(Base):
    __tablename__ = "slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    datetime: Mapped[datetime] = mapped_column(DateTime, index=True)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)

    booking: Mapped[Optional["Booking"]] = relationship(back_populates="slot", uselist=False)

    def __repr__(self) -> str:
        return f"<Slot id={self.id} dt={self.datetime} booked={self.is_booked}>"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id"), unique=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # status: pending / paid / cancelled / done
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="bookings")
    service: Mapped["Service"] = relationship(back_populates="bookings")
    slot: Mapped["Slot"] = relationship(back_populates="booking")

    def __repr__(self) -> str:
        return f"<Booking id={self.id} user={self.user_id} status={self.status}>"