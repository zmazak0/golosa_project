from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup


class Form(StatesGroup):
    text = State()
