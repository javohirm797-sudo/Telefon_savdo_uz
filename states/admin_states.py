from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    admin_password = State()
    broadcast = State()
    delete_ad = State()
