from aiogram.fsm.state import State, StatesGroup

class PostAdStates(StatesGroup):
    brand = State()
    model = State()
    custom_model = State()
    condition = State()
    memory = State()
    battery = State()
    color = State()
    price = State()
    region = State()
    photo = State()          # FAQATGINA 1 DONA rasm
    description = State()
    confirm = State()
