from typing import Any

from db import db_instance


class Talk:
    """
    Talk object saved User's talk state,
    when bot is asking user questions.

    All the intermediate things about talk state
    will also saved in here.

    Use case:
    ```
    talk = Talk(user.line)
    if talk:
        ...  # continue QA
    ...
    # save something in this state
    talk.set('temp', [123])
    talk.save()
    ```

    Structure:
    ```
    [talk-id]: {
        user: str,
        keyword: str,
        label: values
    }
    ```
    """

    db = db_instance

    def __init__(self, line_id: str):
        """Init the Talk instance and query from db immediatly"""
        self.id = "talk-" + line_id
        self.talk = self.db.get(self.id) or {}

    @property
    def keyword(self) -> str:
        """Keyword saved the function name we need to continue on"""
        return self.talk.get("keyword", "")

    def set(self, key: str, value: Any) -> None:
        """Set Any value to this object"""
        self.talk[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """get Any value to this object"""
        return self.talk.get(key, default)

    def clear(self) -> None:
        """Remove this key from DB"""
        if self:
            self.db.delete(self.id)

    def save(self) -> None:
        """Save this instance to DB"""
        assert self.talk
        self.db.set(self.id, self.talk)

    def __bool__(self) -> bool:
        """Whether this talk-key is exists in DB"""
        return bool(set(self.talk) - set(["keyword"]))
