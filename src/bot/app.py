from dotenv import load_dotenv
import os
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

logging.basicConfig(level=logging.INFO)

load_dotenv(".env")
TG_BOT_TOKEN = os.environ['TG_BOT_TOKEN']

bot = Bot(token=TG_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    text = State()


@dp.message_handler(commands="help")
async def show_help(message: types.Message):
    await message.answer(
        text=f"Hi! I'm Golosa bot. I can convert text to speech.")


@dp.message_handler(commands="text")
async def show_text_preview(message: types.Message):
    await Form.text.set()
    await message.reply(text="Please, enter your text:", reply=False)


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.text)
async def process_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text
    audio = types.InputFile("dummy.mp3")
    await message.reply_audio(audio=audio, title=data['text'], reply=False)
    await state.finish()


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_shutdown=shutdown)