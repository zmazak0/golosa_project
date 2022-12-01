from aiogram import types
from dispatcher import dp
from filters import Form
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext


@dp.message_handler(commands="start")
async def show_help(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["О боте", "Синтезировать текст", "Отмена"]
    keyboard.add(*buttons)
    await message.answer(
        text=f"Привет! Бот предназначен для синтеза речи.", reply_markup=keyboard)


@dp.message_handler(text="О боте")
async def show_help(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["О боте", "Синтезировать текст", "Отмена"]
    keyboard.add(*buttons)
    await message.answer(
        text=f"Бот разработала команда Голоса. Бот предназначен для синтеза речи.", reply_markup=keyboard)


@dp.message_handler(text="Синтезировать текст")
async def show_text_preview(message: types.Message):
    await Form.text.set()
    await message.reply(text="Введите текст для синтеза", reply=False)


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
@dp.message_handler(Text(equals='Отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())
