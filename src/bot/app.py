import sys
from dataclasses import dataclass, field
import os
import logging
import requests, json
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from transformers import HfArgumentParser

logging.basicConfig(level=logging.INFO)


@dataclass
class TgArguments:
    bot_token: str = field(default="", metadata={"help": "Bot token."})
    log_path: str = field(default=None, metadata={"help": "Log path."})
    log_error_path: str = field(default=None, metadata={"help": "Log path for fails."})

# парсер аргументов командной строки
parser = HfArgumentParser(TgArguments)
if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
    # If we pass only one argument to the script and it's the path to a json file,
    # let's parse it to get our arguments.
    args = parser.parse_json_file(json_file=os.path.abspath(sys.argv[1]))[0]
else:
    args = parser.parse_args_into_dataclasses()[0]

TG_BOT_TOKEN = args.bot_token
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


# vocalize text
@dp.message_handler(state=Form.text)
async def process_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text
    # audio = types.InputFile("dummy.mp3")
    # Тут надо прикрутить получение предсказания от модельки
    # Ей на вход надо кидать data['text']
    audio = requests.post("http://127.0.0.1:8000/synthesys", data=json.dumps(
        {"text": data['text']})
                          )

    buttons = [
        types.InlineKeyboardButton(text="👍", callback_data="like"),
        types.InlineKeyboardButton(text="👎", callback_data="dislike")
    ]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*buttons)

    await message.reply_audio(audio=audio, title=data['text'], reply=False, reply_markup=keyboard)
    await state.finish()


@dp.callback_query_handler(text=["like", "dislike"])
async def send_random_value(call: types.CallbackQuery):
    await call.message.answer('Спасибо за обратную связь!')


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_shutdown=shutdown)
