# utils/cache_utils.py
from aiocache import Cache
from aiocache.serializers import JsonSerializer
import aiofiles
import json
from config import base_dir, cache_file_path
import os


# класс для работы с кешем
class CacheManager:

    def __init__(self, cache_type=Cache.MEMORY, ttl=43200, **kwargs):
        self.KEY_TRACKER = '__cache_keys__'
        self.cache = Cache(cache_type, serializer=JsonSerializer(), **kwargs)
        self.default_ttl = ttl

    async def set_data(self, key, value, ttl=None):
        ttl = ttl if ttl is not None else self.default_ttl
        await self.cache.set(key, value, ttl=ttl)

        # Добавляем ключ в список отслеживаемых ключей, если он не GLOBAL
        if key != "GLOBAL":  # Исключаем GLOBAL из трекера
            tracked_keys = await self.cache.get(self.KEY_TRACKER) or []
            if key not in tracked_keys:
                tracked_keys.append(key)
                await self.cache.set(self.KEY_TRACKER, tracked_keys)

        print(f"Ключ '{key}' успешно добавлен в кэш.")
        return True

    async def update_data(self, key, new_data):
        existing_data = await self.cache.get(key) or {}
        existing_data.update(new_data)
        await self.cache.set(key, existing_data, ttl=self.default_ttl)
        print(f"Данные по ключу '{key}' успешно обновлены.")
        return True

    async def get_data(self, key):
        print(f"Получение данных по ключу {key}...")
        data = await self.cache.get(key)
        if data is not None:
            print(f"Данные по ключу '{key}' успешно получены.")
        return data

    async def clear_data(self, key, keys_to_remove=None):
        if keys_to_remove is None:
            await self.cache.delete(key)
            print(f"Данные по ключу '{key}' успешно удалены.")
        else:
            data = await self.cache.get(key)
            if data:
                for k in keys_to_remove:
                    data.pop(k, None)
                await self.cache.set(key, data, ttl=self.default_ttl)
                print(
                    f"Ключи {keys_to_remove} удалены из данных по ключу '{key}'.")
        return True

    async def delete(self, key):
        result = await self.cache.delete(key)

        # Обновляем трекер ключей, если ключ не GLOBAL
        if key != "GLOBAL":
            tracked_keys = await self.cache.get(self.KEY_TRACKER) or []
            if key in tracked_keys:
                tracked_keys.remove(key)
                await self.cache.set(self.KEY_TRACKER, tracked_keys)

        print(f"Ключ '{key}' успешно удалён из кэша.")
        return result

    async def get_all_keys(self):
        """Получает все отслеживаемые ключи."""
        return await self.cache.get(self.KEY_TRACKER) or []

    async def save_cache_to_file(self):
        """Сохраняет кэш в файл."""
        try:
            keys = await self.get_all_keys()
            if not keys:  # Don't save if no tracked keys
                return "Кэш пуст. Нечего сохранять."

            all_data = {}
            for key in keys:  # Only save tracked keys
                data = await self.cache.get(key)
                if data:
                    all_data[key] = data

            # Add GLOBAL data if present.
            global_data = await self.cache.get("GLOBAL")
            if global_data:
                all_data["GLOBAL"] = global_data

            full_file_path = os.path.join(base_dir, cache_file_path)
            async with aiofiles.open(full_file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(all_data, ensure_ascii=False, indent=4))

            return f"Кэш сохранён в {cache_file_path} ({len(all_data)} записей)."

        except Exception as e:
            return f"Ошибка сохранения: {e}"

    async def load_cache_from_file(self):
        """Загружает кэш из файла."""
        full_file_path = os.path.join(base_dir, cache_file_path)
        try:
            async with aiofiles.open(full_file_path, 'r', encoding='utf-8') as f:
                content = await f.read()

            if not content.strip():
                return "Файл пуст. Кэш не загружен."

            all_data = json.loads(content)
            count = 0

            for key, value in all_data.items():
                # Use set_data to update tracking.
                await self.set_data(key, value)
                count += 1

            return f"Кэш загружен из {cache_file_path} ({count} записей)."

        except FileNotFoundError:
            return f"Файл {cache_file_path} не найден."
        except json.JSONDecodeError as e:
            return f"Ошибка JSON: {e}"
        except Exception as e:
            return f"Ошибка загрузки: {e}"
