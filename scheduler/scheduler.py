#
import random
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from db.crud import CategoryCRUD
from db.models import SessionLocal

from utils.telegra_ph import get_page
from utils.telegram import send_message_admin


# Функция для напоминания сгенерировать книгу
async def create_book_notification(session):
    cats = await CategoryCRUD.get_all_categories(session)
    cat = random.choice(cats)
    msg = f"Напоминание сгенерировать книгу для: {cat.name}"
    await send_message_admin(msg)


# Установка планировщика
def setup_scheduler():
    """Настраивает и запускает планировщик для различных задач вместе с ботом."""
    session = SessionLocal()
    scheduler = AsyncIOScheduler()

    # Запуск планировщика
    scheduler.start()
