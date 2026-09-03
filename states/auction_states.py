from aiogram.fsm.state import State, StatesGroup

class AuctionCreateStates(StatesGroup):
    brand = State()
    model = State()
    custom_model = State()
    condition = State()
    memory = State()
    battery = State()
    color = State()
    region = State()
    photo = State()
    description = State()
    start_price = State()
    min_step = State()
    duration = State()
    confirm = State()
    receipt = State()

class AuctionBidStates(StatesGroup):
    custom_bid = State()