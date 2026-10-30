from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    """Состояния диалога записи на услугу."""
    choosing_service = State()
    choosing_slot = State()
    confirming = State()


class AdminServiceStates(StatesGroup):
    """Состояния добавления новой услуги (только админ)."""
    name = State()          # ждём название
    price = State()         # ждём цену
    duration = State()      # ждём длительность