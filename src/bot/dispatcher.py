import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv

# Config
load_dotenv(".env")
TG_BOT_TOKEN = os.environ['TG_BOT_TOKEN']

# Configure logging
logging.basicConfig(level=logging.INFO)

# Init bot
bot = Bot(token=TG_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
