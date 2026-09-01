from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from utils import format_owner_info

router = Router()

@router.message(F.text == "👨‍💻 Bog'lanish (Admin)")
@router.message(Command("contact"))
async def show_contact_info(message: Message):
    text = format_owner_info()
    await message.answer(text)
