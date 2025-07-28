from aiogram.fsm.state import StatesGroup, State


class DepositState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_payment = State()