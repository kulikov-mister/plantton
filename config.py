import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.strategy import FSMStrategy
from aiogram.fsm.storage.memory import MemoryStorage

token = os.environ.get("TELEGRAM_API_TOKEN")
bot = Bot(token=token, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher(storage=MemoryStorage(), fsm_strategy=FSMStrategy.CHAT)


admin_ids = [6316305521]
admin_ids_str: int = admin_ids
base_dir = os.path.dirname(os.path.abspath(__file__))
token = os.environ.get("TELEGRAM_API_TOKEN")
is_tech_works = False
