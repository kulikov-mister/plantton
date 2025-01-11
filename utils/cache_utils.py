# utils/cache_utils.py
from aiocache import Cache
from aiocache.serializers import JsonSerializer


# класс для работы с кешем
class CacheManager:
    def __init__(self, cache_type=Cache.MEMORY, ttl=3600, **kwargs):
        self.cache = Cache(cache_type, serializer=JsonSerializer(), **kwargs)
        self.default_ttl = ttl

    async def set_data(self, user_id, user_data, ttl=None):
        ttl = ttl if ttl is not None else self.default_ttl
        await self.cache.set(user_id, user_data, ttl=ttl)

    async def update_data(self, user_id, user_data):
        existing_data = await self.cache.get(user_id) or {}
        existing_data.update(user_data)
        await self.cache.set(user_id, existing_data, ttl=self.default_ttl)

    async def get_data(self, user_id, user_data_keys=None):
        user_data = await self.cache.get(user_id)
        if user_data_keys is None:
            return user_data
        else:
            return {key: user_data.get(key) for key in user_data_keys}

    async def clear_data(self, user_id, user_data_keys=None):
        if user_data_keys is None:
            await self.cache.delete(user_id)
        else:
            user_data = await self.cache.get(user_id)
            if user_data:
                for key in user_data_keys:
                    user_data.pop(key, None)
                await self.cache.set(user_id, user_data, ttl=self.default_ttl)

    async def delete(self, key):
        return await self.cache.delete(key)
