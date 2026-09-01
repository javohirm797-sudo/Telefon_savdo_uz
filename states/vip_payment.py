from aiogram.fsm.state import State, StatesGroup

class VIPPaymentStates(StatesGroup):
    select_plan = State()
    upload_receipt = State()
