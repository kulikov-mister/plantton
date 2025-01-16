# main.py
# основной файл создания книг и загрузки в Telegra.ph
import os
import json
import asyncio
from utils.gemini import GeminiClient
from utils.open_ai import OpenAI
from utils.tools import write_data_file
from utils.telegra_ph import create_book_in_telegraph
from utils.telegram import send_message_admin


gemini_api_key = os.environ.get("GOOGLE_API_KEY")
openai_api_key = os.environ.get("OPENAI_API_KEY")


# генерация глав для книги
async def generate_topics_book(query_topics: str, qt_topics: int = 10, type: str = 'Gemini', gemini_api_key=gemini_api_key, openai_api_key=openai_api_key):
    prompt = f"""
Напиши список из {qt_topics} глав для книги на тему: {query_topics}.
Используй тот язык, на котором написана тема: {query_topics}
Используй list схему:
[ "название 1й главы", "название 2й главы", ..., "название {qt_topics}й главы"]
Верни чистый список без форматирования и лишних символов - [...]
"""
    if type == 'Gemini':
        client = GeminiClient(gemini_api_key)
        result, books_topics = await client.generate_text(prompt)
        books_topics_json = json.loads(books_topics)
    elif type == 'Openai':
        client = OpenAI(openai_api_key)
        result, books_topics = await client.generate_text(prompt)
        print(books_topics)
        # Оборачиваем в квадратные скобки, если это не валидный JSON
        formatted_content = f'[{books_topics}]' if not books_topics.startswith(
            '[') else books_topics
        books_topics_json = json.loads(formatted_content)
    else:
        return None, "Тип генерации не определен"

    if result:
        if not isinstance(books_topics_json, list):
            return None, "Полученные данные не являются списком."
        if len(books_topics_json) < qt_topics:
            return None, "Полученные данные не содержат 10 глав."
        else:
            return True, books_topics_json[:qt_topics]
    else:
        return None, books_topics


# генерация глав для книги
async def generate_themes_book(category: str, qt_themes: int = 10, type: str = 'Gemini', gemini_api_key=gemini_api_key, openai_api_key=openai_api_key):
    prompt = f"""
Представь мы пишем маленькую книгу на академическую тему в категории: {category} объёмом до 10 листов A4.
Напиши список из {qt_themes} таких тем в этой категории, которые были бы интересны широкому кругу читателей.
Темы книги должны быть рандомно на русском или английском языке.
Используй list схему:
[ "название 1й темы", "название 2й темы", ..., "название {qt_themes}й темы"]
Верни чистый список без форматирования и лишних символов - [...]
"""
    if type == 'Gemini':
        client = GeminiClient(gemini_api_key)
        result, books_topics = await client.generate_text(prompt)
        books_topics_json = json.loads(books_topics)
    elif type == 'Openai':
        client = OpenAI(openai_api_key)
        result, books_topics = await client.generate_text(prompt)
        print(books_topics)
        # Оборачиваем в квадратные скобки, если это не валидный JSON
        formatted_content = f'[{books_topics}]' if not books_topics.startswith(
            '[') else books_topics
        books_topics_json = json.loads(formatted_content)
    else:
        return None, "Тип генерации не определен"

    if result:
        if not isinstance(books_topics_json, list):
            return None, "Полученные данные не являются списком."
        if len(books_topics_json) < qt_themes:
            return None, "Полученные данные не содержат 10 глав."
        else:
            return True, books_topics_json[:qt_themes]
    else:
        return None, books_topics


# генерация книги
async def generate_book(query_topics: str, books_topics_json, type: str = 'Gemini', gemini_api_key=gemini_api_key, openai_api_key=openai_api_key):
    if type == 'Gemini':
        client = GeminiClient(gemini_api_key)
    elif type == 'Openai':
        client = OpenAI(openai_api_key)
    else:
        return None, "Тип генерации не определен"

    full_book = {}
    max_retries = 3  # Максимальное количество попыток для каждой главы
    retry_delay = 5  # Задержка перед повторной попыткой

    for bt in books_topics_json:
        for attempt in range(max_retries):  # Цикл попыток для каждой главы
            prompt_topic = f"""
Мы пишем книгу на тему: {query_topics}.
Сейчас напиши подробно главу для этой книги на тему {bt}.
Используй тот язык для главы, на котором написана тема: {query_topics}
Не используй слово - "Глава ..." и прочую нумерацию в заголовках, чтобы не было путаницы.
Используй обязательно частое форматирование и эмодзи для украшения главы.
Верни только текст главы с форматированием без лишних комментариев.
"""
            # Генерация главы
            result, books_topic = await client.generate_text(prompt_topic)

            if result:  # Успешно сгенерировано
                if isinstance(books_topic, list):  # Если список, соединяем
                    books_topic = "\n".join(books_topic)
                elif not isinstance(books_topic, str):  # Преобразуем в строку
                    books_topic = str(books_topic)

                # Добавляем в книгу
                full_book[bt] = books_topic
                break  # Выходим из цикла попыток для этой главы
            else:
                print(f"Ошибка генерации для главы '{bt}': {books_topic}")
                if attempt < max_retries - 1:
                    print(f"Повторная попытка для главы '{
                          bt}' через {retry_delay} секунд...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"Не удалось сгенерировать главу '{
                          bt}' после {max_retries} попыток.")
                    full_book[bt] = f"Не удалось сгенерировать главу: {
                        books_topic}"

        # Пауза перед следующей главой
        await asyncio.sleep(3)

    return full_book


# старт создания книги
async def start_create():
    query_topics = input('Введите тему для книги: ')
    if not query_topics:
        print("Тема для книги не может быть пустой.")
        return
    client = GeminiClient(gemini_api_key)

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
