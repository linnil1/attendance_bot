from __future__ import annotations
from typing import Any
from datetime import datetime

from base import Base


class History(Base):
    """
    The history of user response to report

    Structure:
    ```
    [history-reportid-user_id]:
        id: str
        report: ID
        user: ID
        history: [json-info]
    """

    def __init__(self, report_id: str, user_id: str):
        super().__init__(f"history-{report_id}-{user_id}")
        self._default = {
            "id": self.id,
            "report": report_id,
            "user": user_id,
            "history": [],
        }

    def addResponse(self, data: Any) -> None:
        """User response to the report and save here"""
        data["time"] = datetime.now()
        self["history"].append(data)
