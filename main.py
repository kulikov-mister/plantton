# main.py
# основной файл создания книг и загрузки в Telegra.ph
import os
import json
import asyncio
from tqdm.asyncio import tqdm
from utils.gemini import GeminiClient
from utils.tools import write_data_file
from utils.telegra_ph import create_book_in_telegraph
from utils.telegram import send_message_admin


google_api_key = os.environ.get("GOOGLE_API_KEY")


async def generate_topics_book(query_topics: str, qt_topics: int = 10):
    client = GeminiClient(google_api_key)
    prompt = f"""
Напиши список из {qt_topics} глав для книги на тему: {query_topics}.
Используй тот язык, на котором написана тема: {query_topics}
Используй list схему:
[ "название 1й главы", "название 2й главы", ..., "название {qt_topics}й главы"]
Верни чистый список без форматирования и лишних символов - [...]
"""
    result, books_topics = await client.generate_text(prompt)
    books_topics_json = json.loads(books_topics)

    if result:
        if not isinstance(books_topics_json, list):
            return None, "Полученные данные не являются списком."
        if len(books_topics_json) < qt_topics:
            return None, "Полученные данные не содержат 10 глав."
        else:
            return True, books_topics_json[:qt_topics]
    else:
        return None, books_topics


#
async def generate_book(query_topics: str, books_topics_json, ):
    client = GeminiClient(google_api_key)
    full_book = {}
    # for bt in tqdm(books_topics_json, desc='Генерация книги'):
    for bt in books_topics_json:
        prompt_topic = f"""
Мы пишем книгу на тему: {query_topics}.
Сейчас напиши подробно главу для этой книги на тему {bt}.
Используй тот язык для главы, на котором написана тема: {query_topics}
Не используй слово - "Глава ..." и прочую нумерацию в заголовках, чтобы не было путаницы.
Используй обязательно частое форматирование и эмодзи для украшения главы.
Верни только текст главы с форматированием без лишних комментариев.
"""
        # генерация частей книги
        result, books_topic = await client.generate_text(prompt_topic)
        if result:
            # Если пришёл список, соединяем элементы в строку с переносами
            if isinstance(books_topic, list):
                books_topic = "\n".join(books_topic)
            # Преобразуем в строку, если это другой тип данных
            elif not isinstance(books_topic, str):
                books_topic = str(books_topic)

            # Добавляем в книгу
            full_book[bt] = books_topic

            # пауза перед следующей главой
            await asyncio.sleep(3)
    # возврат полной книги
    return full_book


# старт создания книги
async def start_create():
    query_topics = input('Введите тему для книги: ')
    if not query_topics:
        print("Тема для книги не может быть пустой.")
        return
    client = GeminiClient(google_api_key)

    try:
        # генерация книги
        books_topics, full_book = await generate_book(client, query_topics)
        if not books_topics:
            print('Главы для книги не созданы')
            return
        if not full_book:
            print('Книга не создана или пустая')
            return
        # сохранение книги в файл
        books_data = json.dumps({
            'book_name': query_topics,
            'books_topics': books_topics,
            'full_book': full_book
        }, ensure_ascii=False, indent=4)
        await write_data_file(f'history/{query_topics}.json', books_data)
        # print("Успешно сохранили книгу")
        # book_data = await read_data_file(f'history/{query_topics}.json')
        # создаем книгу в телеграфе
        book_url = await create_book_in_telegraph(json.loads(books_data))
        book_link_html = f'<a href="{book_url}">{query_topics}</a>'
        await send_message_admin(book_link_html)

    except json.JSONDecodeError as e:
        print(
            f"Ошибка декодирования JSON: {e}. Строка не является корректным JSON.")

    except Exception as e:
        print(f"Произошла ошибка: {e}")


# старт бота
# if __name__ == "__main__":
#     asyncio.run(start_create())
