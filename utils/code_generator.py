import random
import string
import asyncio


async def generate_random_string_async(length=10):
    """
    Асинхронная функция для генерации случайной строки из заглавных букв и цифр.

    :param length: Длина генерируемой строки.
    :return: Сгенерированная строка.
    """
    # Генерация строки из заглавных букв и цифр
    characters = string.ascii_uppercase + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


async def generate_random_string_async_lower(length=10):
    """
    Асинхронная функция для генерации случайной строки из заглавных букв и цифр.
    """
    # Генерация строки из заглавных букв и цифр
    characters = string.ascii_lowercase + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


async def some_function():
    random_string = await generate_random_string_async_lower(12)
    print(random_string)

# asyncio.run(some_function())
