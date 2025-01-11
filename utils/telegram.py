# utils/telegram.py
from config import bot


# отправка сообщения админу
async def send_message_admin(message: str, chat_id: str = '6316305521'):
    await bot.send_message(chat_id, message, parse_mode='HTML')


# msg = '<a href="https://telegra.ph/Obuchenie-russkomu-yazyku-s-pomoshchyu-Telegram-bota-v-stranah-SNG-12-31">Обучение русскому языку с помощью Telegram бота в странах СНГ</a>'
# asyncio.run(send_message(msg))
