from aiogram.fsm.state import (
    State,
    StatesGroup,
)


class CheckIn(StatesGroup):

    waiting_passport = State()

    waiting_receipt = State()
