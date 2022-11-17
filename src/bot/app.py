import asyncio
from dotenv import load_dotenv
import os
import logging
import json
import string
import random
import commands
from dotenv import load_dotenv
from aiogram import Dispatcher, types, executor
from dispatcher import dp, bot
from filters import Form
from aiogram.dispatcher import FSMContext
from redis import Redis
from datetime import datetime
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth, ServiceAccountCredentials

gauth = GoogleAuth()
scope = ['https://www.googleapis.com/auth/drive']

gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name("creds/client_secrets.json", scope)
drive = GoogleDrive(gauth)

redis_client = Redis(host=REDIS_HOSTNAME, port=REDIS_PORT, db=0)
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


@dp.message_handler(content_types=[types.ContentType.VOICE])
async def voice_message_handler(message: types.Message):
    file = await message.voice.get_file()
    file_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    file_path = f'{file_name}.ogg'
    await bot.download_file(file_path=file.file_path, destination=file_path)

    f = drive.CreateFile({'title': f'{file_name}.ogg', 'parents': [{'id': GDRIVE_FOLDER_ID}]})
    f.SetContentFile(f'{file_name}.ogg')
    f.Upload()
    os.remove(file_path)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(get_audio())
    executor.start_polling(dp, skip_updates=True, on_shutdown=shutdown)
