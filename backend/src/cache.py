import redis
from typing import Optional, Any
from json import dumps, loads

from .config import settings

class Cache:
    def __init__(self, url: str = settings.redis_url):
        self.client = redis.from_url(url)
    
    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.client.get(key)
            if value is None:
                return None
            return loads(value.decode("utf-8"))
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = None) -> bool:
        try:
            serialized = dumps(value)
            if expire:
                self.client.setex(key, expire, serialized)
            else:
                self.client.set(key, serialized)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False

cache = Cache()
