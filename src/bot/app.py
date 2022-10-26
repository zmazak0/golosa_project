import asyncio
from dotenv import load_dotenv
import os
import logging
import json
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from redis import Redis
from datetime import datetime

logging.basicConfig(level=logging.INFO)

load_dotenv(".env")
TG_BOT_TOKEN = os.environ['TG_BOT_TOKEN']

bot = Bot(token=TG_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

redis_client = Redis(host="0.0.0.0", port=6379, db=0)
redis_subscriber = redis_client.pubsub()
redis_subscriber.subscribe("audio")


async def get_audio():
    buttons = [
        types.InlineKeyboardButton(text="👍", callback_data="like"),
        types.InlineKeyboardButton(text="👎", callback_data="dislike")
    ]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*buttons)
    while True:
        message = redis_subscriber.get_message()
        if message and message['type'] == "message":
            channel = message['channel'].decode("utf-8")
            response = json.loads(message['data'].decode("utf-8"))
            print("Input:", response)
            if channel == "audio":
                await bot.send_audio(
                    chat_id=response['chat_id'],
                    audio=bytes(response['audio']),
                    title=f"audio_{datetime.now().strftime('%Y%m%d_%H_%M_%S')}",
                    reply_markup=keyboard
                )
        await asyncio.sleep(0.1)


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

    request = {
        'text': data['text'],
        'chat_id': message.chat.id
    }
    print("Output:", request)
    redis_client.publish(channel="text", message=json.dumps(request))

    await state.finish()


@dp.callback_query_handler(text=["like", "dislike"])
async def send_random_value(call: types.CallbackQuery):
    await call.message.answer('Спасибо за обратную связь!')


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(get_audio())
    executor.start_polling(dp, skip_updates=True, on_shutdown=shutdown)
