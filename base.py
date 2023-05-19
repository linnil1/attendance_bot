from typing import Self, Any
from db import db_instance


class Base:
    """
    The base class of team/user/report
    """

    db = db_instance

    def __init__(self, key: str):
        self.id = key
        self.lock: Any = None  # Redlock object if db is redis
        self._object: Any = None
        self._default: Any = None

    @classmethod
    def create(cls, *args: Any, **kwargs: Any) -> Self:
        """Create method"""
        raise NotImplementedError

    @classmethod
    def newObject(cls, prefix: str, data: Any) -> Self:
        """Create method"""
        obj = cls(cls.db.create(prefix))
        obj._object = data
        obj._object["id"] = obj.id
        return obj

    @property
    def object(self) -> Any:
        """Query DB if _object is None and init data if requires creation"""
        if self._object is None:
            self._object = self.db.get(self.id)
        if self._object is None:
            self._object = self._default
        return self._object

    def __bool__(self) -> bool:
        """Is this token exists"""
        return bool(self.object)

    def __getitem__(self, ind: str) -> Any:
        """getter"""
        return self.object[ind]

    def __setitem__(self, ind: str, value: Any) -> None:
        """setter"""
        self.object[ind] = value

    def save(self) -> None:
        """Save to DB"""
        assert self._object
        self.db.set(self.id, self._object)
        if self.lock and self.lock.locked():
            self.lock.release()
        self.lock = None

    def block(self) -> None:
        """Block team to be written and give the latest team"""
        self.lock = self.db.lock(self.id)
        self._object = None
