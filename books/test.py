#
import random
import json
import asyncio
from utils.tools import write_data_file
from db.crud import BookCRUD, CategoryCRUD
from db.models import SessionLocal
from creator import generate_themes_book
from tqdm.asyncio import tqdm

session = SessionLocal()


# Функция для напоминания сгенерировать книгу
async def auto_book_creator(session):
    # cats = await CategoryCRUD.get_all_categories(session)
    # cat = random.choice(cats)
    ...


async def auto_themes_creator():
    cats = await CategoryCRUD.get_all_categories(session)
    all_themes = {}
    for cat in tqdm(cats, 'Generating themes'):
        themes = await generate_themes_book(cat.name)
        all_themes[cat] = themes
        print('---', themes, '---', sep='\n')
        await asyncio.sleep(5)
    all_themes_data = json.dumps(all_themes, ensure_ascii=False, indent=4)
    await write_data_file(f'books/all_themes.json', all_themes_data)
    return all_themes

if __name__ == "__main__":
    asyncio.run(auto_themes_creator)
