from typing import Any
from pprint import pformat
from datetime import timedelta
import uuid
import logging

# for redis
from pottery import Redlock
from redis import Redis
import orjson

# for dynamodb
import boto3
from python_dynamodb_lock.python_dynamodb_lock import DynamoDBLockClient, DynamoDBLock

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


class DynamoDB:
    """
    A KV storage of AWS
    """

    logger = logging.getLogger("attendence.db")

    def __init__(self) -> None:
        """Connect to redis instance"""
        self.dynamo_client = boto3.client("dynamodb")
        self.dynamo_resource = boto3.resource("dynamodb")
        self.createTable()
        self.createLockTable()

    def createLockTable(self) -> None:
        """
        Create Lock table
        However, there is not official implemented package.
        I use outdated https://github.com/mohankishore/python_dynamodb_lock.
        Maybe I'll change it
        """
        self.lock_client = DynamoDBLockClient(
            self.dynamo_resource,
            table_name=settings.dynamodb_table + "-lock",
            expiry_period=timedelta(seconds=30),
        )
        try:
            self.logger.info(f"Creating {self.lock_client._table_name}")
            db_lock = self.dynamo_resource.create_table(
                TableName=self.lock_client._table_name,
                KeySchema=[
                    {
                        "AttributeName": self.lock_client._partition_key_name,
                        "KeyType": "HASH",
                    },
                    {
                        "AttributeName": self.lock_client._sort_key_name,
                        "KeyType": "RANGE",
                    },
                ],
                AttributeDefinitions=[
                    {
                        "AttributeName": self.lock_client._partition_key_name,
                        "AttributeType": "S",
                    },
                    {
                        "AttributeName": self.lock_client._sort_key_name,
                        "AttributeType": "S",
                    },
                ],
                **settings.dynamodb_other,
            )
            db_lock.wait_until_exists()
            self.dynamo_client.update_time_to_live(
                TableName=self.lock_client._table_name,
                TimeToLiveSpecification={
                    "Enabled": True,
                    "AttributeName": self.lock_client._ttl_attribute_name,
                },
            )
            db_lock.wait_until_exists()

        except boto3.exceptions.botocore.exceptions.ClientError:
            self.logger.info(f"{self.lock_client._table_name} has created")
            pass

    def createTable(self) -> None:
        """Create or use the table"""
        try:
            self.db = self.dynamo_resource.create_table(
                TableName=settings.dynamodb_table,
                KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
                AttributeDefinitions=[
                    {"AttributeName": "id", "AttributeType": "S"},
                ],
                **settings.dynamodb_other,
            )
            self.db.wait_until_exists()
            self.logger.info(f"Create {self.db}")
        except boto3.exceptions.botocore.exceptions.ClientError:
            self.db = self.dynamo_resource.Table(settings.dynamodb_table)
            self.logger.info(f"Use existed {self.db}")

    def clear(self) -> None:
        """Remove all data"""
        self.logger.info(f"Delete {self.db}")
        self.db.delete()
        db_lock = self.dynamo_resource.Table(self.lock_client._table_name)
        self.logger.info(f"Delete {db_lock}")
        db_lock.delete()
        self.db.wait_until_not_exists()
        db_lock.wait_until_not_exists()
        self.createTable()
        self.createLockTable()

    @classmethod
    def isLock(cls, lock: DynamoDBLock) -> bool:
        """Lock status"""
        return lock.status == "LOCKED"  # type: ignore

    @classmethod
    def release(cls, lock: DynamoDBLock) -> None:
        """Release lock"""
        lock.release()

    def lock(self, key: str) -> DynamoDBLock:
        """Block the execution depended on the key"""
        return self.lock_client.acquire_lock(key)

    def get(self, key: str, default: Any | None = None) -> Any:
        """Get Data by key"""
        raw_value = self.db.get_item(Key={"id": key}).get("Item")
        if not raw_value:
            return default
        value = orjson.loads(raw_value["data"].value)
        self.logger.debug(f"Get {key}={value}")
        return value
        # directly save dict into db
        # return raw_value

    def set(self, key: str, value: Any) -> None:
        """Set data by key"""
        # why dynamodb not support time
        # directly save dict into db
        # value['id'] = key
        # self.db.put_item(Item=value)
        self.db.put_item(Item={"id": key, "data": orjson.dumps(value)})
        self.logger.debug(f"Set {key}=\n{pformat(value)}")

    def gets(self, keys: list[str]) -> list[Any]:
        """Get Data by keys"""
        raise NotImplementedError

    def sets(self, key_values: list[tuple[str, Any]]) -> None:
        """Set data by keys and values"""
        raise NotImplementedError
        # with self.db.batch_writer() as writer:
        #     for key, value in key_values:
        #         value['id'] = key
        #         writer.put_item(Item=value)

    def delete(self, key: str) -> None:
        """Delete key"""
        self.db.delete_item(Key={"id": key})
        self.logger.debug(f"Delete {key}")

    def create(self, prefix: str) -> str:
        """Find a random and unused key"""
        while True:
            key = prefix + str(uuid.uuid4())
            if not self.get(key):
                break
        return key


if settings.db == "object":
    db_instance = KVData()
elif settings.db == "redis":
    db_instance = RedisDB()
elif settings.db == "dynamodb":
    db_instance = DynamoDB()
else:
    raise ValueError(f"DB type {settings.db} not found")
if settings.mode == "test":
    db_instance.clear()
