# tools/tools.py
import aiofiles
import json
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def append_line_to_file(filename, line):
    """Асинхронно добавляет строку в конец текстового файла."""

    filepath = os.path.join(base_dir, filename)
    async with aiofiles.open(filepath, 'a', encoding='utf-8') as file:
        try:
            # Добавляем перевод строки для новой строки
            await file.write(line + '\n')
        except Exception as e:
            print(f"Error appending to file: {e}")


# Асинхронное чтение JSON-файла и возврат данных в подходящем формате
async def read_data_file(filename):
    filepath = os.path.join(base_dir, filename)
    if os.path.exists(filepath):
        async with aiofiles.open(filepath, 'r', encoding='utf-8') as file:
            all_data = await file.read()

            # Попытка десериализовать JSON-данные
            try:
                data = json.loads(all_data)

                # Проверка типа данных и возврат в нужном формате
                if isinstance(data, list):
                    return data  # возвращаем, если это список
                else:
                    # если это не список, возвращаем данные как есть (например, словарь)
                    return data

            except json.JSONDecodeError:
                # Если данные не в формате JSON, возвращаем их как обычный текст
                # print("Warning: File content is not valid JSON")
                return all_data

    # Если файла не существует, возвращаем None
    else:
        return None


# Асинхронная функция для записи данных в файл JSON
async def write_data_file(filename, data):
    filepath = os.path.join(base_dir, filename)
    async with aiofiles.open(filepath, 'w', encoding='utf-8') as file:
        try:
            # Записываем данные напрямую
            await file.write(data)
        except TypeError as e:
            print(f"Error writing to file: {e}")
