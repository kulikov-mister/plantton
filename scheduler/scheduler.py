#
import random
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from db.crud import BookCRUD, CategoryCRUD
from db.models import SessionLocal

from utils.telegra_ph import get_page
from utils.telegram import send_message_admin


# Функция для обновления статистики просмотров книг
async def update_views(session):
    """Обновляет статистику просмотров книг и отправляет отчет."""
    books = await BookCRUD.get_all_books(session)

    async def get_page_sem(url):
        async with asyncio.Semaphore(30):
            return await get_page(url)

    # Сбор всех задач и их выполнение
    tasks = [asyncio.create_task(get_page_sem(b.book_url)) for b in books]
    res = await asyncio.gather(*tasks)

    # Формирование текста отчета
    books_stat = ''.join(
        [f'<b>- {i}</b>. <a href="{r.get("url")}">{r.get("title")}</a> | Views: {r.get("views")}\n'
         for i, r in enumerate(sorted(res, key=lambda p: p.get('views'), reverse=True)[:7], start=1)]
    )
    books_stat_msg = '<b>Топ 10 книг месяца:</b>\n\n'+books_stat
    # Отправка отчета
    await send_message_admin(books_stat_msg)
    await send_message_admin(books_stat_msg, '@app5_news')


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

    # обновление статистики 1-го числа в 00:00)
    scheduler.add_job(
        update_views, CronTrigger(day=1, hour=00, minute=0), kwargs={'session': session}
    )

    # напоминание сделать книгу каждый час
    scheduler.add_job(
        create_book_notification, CronTrigger(day=15, hour=17, minute=53), kwargs={'session': session}
    )

    # Запуск планировщика
    scheduler.start()
