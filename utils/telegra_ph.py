# tools/telegra.ph.py
import asyncio
import json

import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions.extra import ExtraExtension
from bleach import Cleaner

from telegraph.aio import Telegraph
from telegraph.utils import ALLOWED_TAGS


# Converts markdown text to HTML, sanitizing the output and modifying header levels.
async def markdown_to_html(markdown_text: str) -> str:
    # Use ExtraExtension for additional features like code highlighting
    html = markdown.markdown(markdown_text, extensions=[
                             ExtraExtension(), HeaderTransformerExtension()])

    # Sanitize HTML with bleach
    cleaner = Cleaner(
        tags=ALLOWED_TAGS,
        attributes={'a': ['href', 'title'], 'img': ['src', 'alt'], 'iframe': [
            # Allow necessary attributes
            'src', 'width', 'height'], 'video': ['src', 'controls']},
        strip=True,  # Remove disallowed tags and attributes instead of escaping
    )
    sanitized_html = cleaner.clean(html)

    return sanitized_html


class HeaderTransformer(Treeprocessor):
    def run(self, root):
        for element in root.iter():
            if element.tag in ('h1', 'h2', 'h3'):
                element.tag = 'h3'
            elif element.tag in ('h4', 'h5', 'h6'):
                element.tag = 'h4'
        return root


class HeaderTransformerExtension(markdown.Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(
            HeaderTransformer(md), 'header_transformer', 5)


# создаёт страницу без токена
async def create_page_without_token(
    first_name: str, title: str, html_content: str, author_name: str = 'App 5', author_url: str = 'https://t.me/app5_bot', return_content: bool = False
) -> None:
    telegraph = Telegraph()
    # create account
    account = await telegraph.create_account(first_name, author_name=author_name, author_url=author_url)
    # print(account)

    # create page
    page = await telegraph.create_page(title, None, html_content, author_name, author_url, return_content)
    return account, page


# создаёт страницу с токеном
async def create_page_with_token(
    access_token: str, title: str, html_content: str, author_name: str = 'App 5', author_url: str = 'https://t.me/app5_bot', return_content: bool = False
) -> None:
    telegraph = Telegraph(access_token=access_token)
    return await telegraph.create_page(title, None, html_content, author_name, author_url, return_content)


# редактирует страницу с токеном
async def edit_page_with_token(
        access_token: str, path: str, title: str, html_content: str, author_name: str = 'App 5', author_url: str = 'https://t.me/app5_bot', return_content: bool = False
) -> None:
    telegraph = Telegraph(access_token=access_token)
    return await telegraph.edit_page(
        path, title, None, html_content, author_name, author_url, return_content
    )


# Асинхронно генерирует HTML-контент для содержания книги.
async def generate_list_topics_html(books_topics, topic_link: bool = False) -> None:
    books_content = f'<h3>Содержание</h3>\n<ol>\n'
    # если в списке глав нет ссылок.
    if not topic_link:
        topic_link = 'https://telegra.ph/Hey-12-27-61'  # ссылка-затычка
        for topic in books_topics:
            books_content += f'<li><a href="{topic_link}">{topic}</a></li>\n'
    else:
        # если в списке глав есть ссылки.
        for topic, topic_link in books_topics.items():
            books_content += f'<li><a href="{topic_link}">{topic}</a></li>\n'

    books_content += '</ol>'  # Конец упорядоченного списка
    # print(books_content, '\n- - - -\n')
    return books_content


# Асинхронно загружает книгу в Telegraph и сохраняет в бд.
async def create_book_in_telegraph(first_name: str, book_data, profile_name: str, profile_link: str):
    # чтение данных книги
    book_name = book_data.get('book_name')
    # print(book_name)

    # главы книги
    books_topics = book_data.get('books_topics')
    # генерация HTML-контента для пустого содержания книги
    html_topics = await generate_list_topics_html(books_topics)
    # создание аккаунта и первоначального содержания книги
    account, page_topics = await create_page_without_token(first_name, book_name, html_topics, profile_name, profile_link)

    access_token = account.get('access_token')  # token
    topics_path = page_topics.get('path')  # путь до содержания
    topics_url = page_topics.get('url')

    # названия глав с содержанием
    full_book = book_data.get('full_book')
    complete_book = {}
    complete_book_data = []
    # for n, c in tqdm(full_book.items(), desc='ЗАГРУЗКА КНИГИ:'):
    for n, c in full_book.items():
        # конвертация markdown статьи в html
        html_c = await markdown_to_html(c)

        # создание страницы содержания главы
        topic_page = await create_page_with_token(access_token, n, html_c, profile_name, profile_link)
        # ссылка на страницу
        topic_url = topic_page.get('url')
        topic_path = topic_page.get('path')
        # добавляем в словарь название статьи с ссылкой
        complete_book[n] = topic_url
        # добавляем в полный словарь в формате json
        complete_book_data.append({
            'name': n,
            'content': html_c,
            'url': topic_url,
            'path': topic_path
        })
        await asyncio.sleep(1)
    complete_book_full = json.dumps(
        complete_book_data, ensure_ascii=False, indent=4)

    # обновление содержания с указанием реальных ссылок на главы
    edit_topics = await generate_list_topics_html(complete_book, True)
    edit_topics_page = await edit_page_with_token(access_token, topics_path, book_name, edit_topics, profile_name, profile_link)
    await asyncio.sleep(2)

    # convert JSON string to Python object
    complete_book = json.loads(complete_book_full)
    num_pages = len(complete_book)  # Если complete_book - список словарей

    # обновление страниц книги с добавлением пагинации
    # Итерируемся по списку словарей
    # for i, chapter in enumerate(tqdm(complete_book, desc='ОБНОВЛЕНИЕ ГЛАВ КНИГИ:')):
    for i, chapter in enumerate(complete_book):

        name = chapter.get('name')
        content = chapter.get('content')
        path = chapter.get('path')

        # ссылки для пагинации
        html_center = f'\n - <a href="{topics_url}"><b>СОДЕРЖАНИЕ</b></a> - '

        # предыдущая ссылка
        html_prev = ''
        if i > 0:
            prev_url = complete_book[i - 1].get('url')
            # Get previous chapter name
            # prev_name = complete_book[i - 1].get('name')
            html_prev = f'<a href="{prev_url}"><b> <<<- </b></a> - '

        # следующая ссылка
        html_next = ''
        if i < num_pages - 1:
            next_url = complete_book[i + 1].get('url')
            # Get next chapter name
            # next_name = complete_book[i + 1].get('name')
            html_next = f'\n - <a href="{next_url}"><b> ->>> </b></a>'

        # строка с ссылками пагинации
        pagin_str = f'{html_prev}\n{html_center}\n{html_next}'
        # формирование обновленного контента
        full_content = f"{pagin_str}\n\n{content}\n\n{pagin_str}"

        # обновление содержимого страницы
        await edit_page_with_token(access_token, path, name, full_content, profile_name, profile_link)
        await asyncio.sleep(1)  # пауза против флуд-контроля

    book_url = edit_topics_page.get('url')
    if book_url:
        return book_url, access_token
    else:
        return None

#
# asyncio.run(create_book_in_telegraph())
