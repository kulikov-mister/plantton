import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.strategy import FSMStrategy
from aiogram.fsm.storage.memory import MemoryStorage

token = os.environ.get("TELEGRAM_API_TOKEN")
bot = Bot(token=token, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher(storage=MemoryStorage(), fsm_strategy=FSMStrategy.CHAT)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL")


admin_ids = [6316305521]
admin_ids_str: int = admin_ids
base_dir = os.path.dirname(os.path.abspath(__file__))
is_tech_works = False
cache_file_path = "bot_cache.json"

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
