from typing import Any
from pprint import pformat
import logging
import uuid

# for redis
from pottery import Redlock
from redis import Redis
import orjson

import settings


class KVData:
    """
    A key-value storage interface
    """

    logger = logging.getLogger("attendence.db")

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}

    def get(self, key: str, default: Any | None = None) -> Any:
        """Get Data by key"""
        value = self.data.get(key, default)
        self.logger.debug(f"Get {key}={value}")
        return value

    def set(self, key: str, value: Any) -> None:
        """Set data by key"""
        self.logger.debug(f"Set {key}={pformat(value)}")
        self.data[key] = value

    def gets(self, keys: list[str]) -> list[Any]:
        """Get Data by keys"""
        return [self.get(key) for key in keys]

    def sets(self, key_values: list[tuple[str, Any]]) -> None:
        """Set data by keys and values"""
        for key, value in key_values:
            self.set(key, value)

    def delete(self, key: str) -> None:
        """Delete key"""
        self.logger.debug(f"Delete {key}")
        del self.data[key]

    def create(self, prefix: str) -> str:
        """Find a random and unused key"""
        while True:
            key = prefix + str(uuid.uuid4())
            if not self.get(key):
                break
        return key

    def clear(self) -> None:
        """Remove all data"""
        self.data = {}

    def lock(self, key: str) -> None:
        """Not implement"""


class RedisDB:
    """
    A key-value storage interface
    """

    logger = logging.getLogger("attendence.db")

    def __init__(self) -> None:
        """Connect to redis instance"""
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    def clear(self) -> None:
        """Remove all data"""
        self.redis.flushall()

    def lock(self, key: str) -> Redlock:
        """Block the execution depended on the key"""
        lock = Redlock(key=key, masters={self.redis}, auto_release_time=0.5)
        lock.acquire()
        return lock

    def get(self, key: str, default: Any | None = None) -> Any:
        """Get Data by key"""
        raw_value = self.redis.get(key)
        if not raw_value:
            return default
        value = orjson.loads(raw_value)
        self.logger.debug(f"Get {key}={value}")
        return value

    def set(self, key: str, value: Any) -> None:
        """Set data by key"""
        self.redis.set(key, orjson.dumps(value))
        self.logger.debug(f"Set {key}=\n{pformat(value)}")

    def gets(self, keys: list[str]) -> list[Any]:
        """Get Data by keys"""
        pipe = self.redis.pipeline()
        [pipe.get(key) for key in keys]
        return [orjson.loads(raw_value) for raw_value in pipe.execute()]

    def sets(self, key_values: list[tuple[str, Any]]) -> None:
        """Set data by keys and values"""
        pipe = self.redis.pipeline()
        [pipe.set(key, orjson.dumps(value)) for key, value in key_values]
        pipe.execute()

    def delete(self, key: str) -> None:
        """Delete key"""
        self.redis.delete(key)
        self.logger.debug(f"Delete {key}")

    def create(self, prefix: str) -> str:
        """Find a random and unused key"""
        while True:
            key = prefix + str(uuid.uuid4())
            if not self.redis.exists(key):
                break
        return key


# db_instance = KVData()
db_instance = RedisDB()
if settings.mode == "test":
    db_instance.clear()
