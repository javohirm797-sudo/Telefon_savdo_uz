from aiogram.fsm.state import State, StatesGroup

class RegisterStates(StatesGroup):
    full_name = State()
    phone_number = State()
