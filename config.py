import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.strategy import FSMStrategy
from aiogram.fsm.storage.memory import MemoryStorage

token = os.environ.get("TELEGRAM_API_TOKEN")
bot = Bot(token=token, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher(storage=MemoryStorage(), fsm_strategy=FSMStrategy.CHAT)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL")
get_file_url = f'https://api.telegram.org/file/bot{token}/'

admin_ids = [6316305521]
admin_ids_str: int = admin_ids
base_dir = os.path.dirname(os.path.abspath(__file__))
is_tech_works = False
cache_file_path = "bot_cache.json"

thumbnails_books = [
    'https://i.imgur.com/rBNKcGs.png', 'https://i.imgur.com/rnuJ2HT.png', 'https://i.imgur.com/wh48b4h.png',
    'https://i.imgur.com/laqMQ7U.png', 'https://i.imgur.com/6uxmLiT.png', 'https://i.imgur.com/0TyC0Rl.png',
    'https://i.imgur.com/FV2rTP9.png', 'https://i.imgur.com/KO4NPNV.png', 'https://i.imgur.com/hJ44lOO.png',
    'https://i.imgur.com/HYcT5eS.png', 'https://i.imgur.com/M27LPcF.png', 'https://i.imgur.com/Y0uVB8U.png',
    'https://i.imgur.com/eqlyruJ.png', 'https://i.imgur.com/TYptKyV.png'
]
thumbnail_default = 'https://i.imgur.com/2dLhsnL.png'
