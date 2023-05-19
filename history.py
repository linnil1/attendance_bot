from __future__ import annotations
from typing import Any
from datetime import datetime

from db import KVData, db_instance


class History:
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

    db = db_instance

    def __init__(self, report_id: str, user_id: str):
        self.id = f"history-{report_id}-{user_id}"
        self.history = self.db.get(
            self.id,
            {
                "id": self.id,
                "report": report_id,
                "user": user_id,
                "history": [],
            },
        )

    def addResponse(self, data: Any) -> None:
        """User response to the report and save here"""
        data["time"] = datetime.now()
        self.history["history"].append(data)

    def save(self) -> None:
        """Save to DB"""
        self.db.set(self.id, self.history)
