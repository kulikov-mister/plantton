#
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

from db.crud import BookCRUD
from db.models import SessionLocal

from utils.telegra_ph import get_page
from utils.telegram import send_message_admin


# Функция для обновления статистики просмотров книг
async def update_views(session):
    """Обновляет статистику просмотров книг и отправляет отчет."""
    books = await BookCRUD.get_all_books(session)

    # Ограничение потоков с использованием семафора
    semaphore = asyncio.Semaphore(30)

    async def get_page_sem(url):
        async with semaphore:
            return await get_page(url)

    # Сбор всех задач и их выполнение
    tasks = [asyncio.create_task(get_page_sem(b.book_url)) for b in books]
    res = await asyncio.gather(*tasks)

    # Формирование текста отчета
    books_stat = ''.join(
        [f'<b>- {i}</b>. <a href="{r.get("url")}">{r.get("title")}</a> | Views: {r.get("views")}\n'
         for i, r in enumerate(sorted(res, key=lambda p: p.get('views'), reverse=True)[:7], start=1)]
    )
    report_text = f'<b>Самые просматриваемые книги месяца:</b>\n\n{books_stat}'

    # Отправка отчета
    await send_message_admin(report_text)


# Планировщик
def setup_scheduler():
    """Настраивает и запускает планировщик для обновления статистики."""
    session = SessionLocal()
    scheduler = AsyncIOScheduler()

    # Добавляем задачу с запуском раз в месяц (например, 1-го числа в 10:00)
    scheduler.add_job(
        update_views, CronTrigger(day=13, hour=19, minute=13), kwargs={'session': session}
    )

    # Запуск планировщика
    scheduler.start()
