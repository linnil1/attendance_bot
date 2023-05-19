from __future__ import annotations
from typing import Any, TYPE_CHECKING

from question import Question
from error import UserInputError
from base import Base


if TYPE_CHECKING:
    from user import User
    from team import Team


class Report(Base):
    """
    Report object.
    Each team has many report wait for user to fill up.

    Structure:
    ```
    [report-id]:
        id: str
        name: str
        team: str
        end: bool
        questions: [Question]
        users:
            [user-id]:
                answer: json-info
    """

    # def __init__(self, report_id: str):
    #     super().__init__(report_id)

    @classmethod
    def create(cls, name: str, team: "Team", questions: list[Question]) -> Report:
        """Create method"""
        return cls.newObject(
            "report-",
            {
                "end": False,
                "name": name,
                "team": team.id,
                "team_name": team.getName(),
                "users": {},
                "questions": questions,  # orjson serialize dataclass by asdict
            },
        )

    def getName(self) -> str:
        """Get report name"""
        return str(self["name"])

    def getTeam(self) -> str:
        """Get report name"""
        return str(self["team"])

    def addResponse(self, user: "User", result: Any) -> None:
        """User response to report and save here"""
        if self["end"]:
            raise UserInputError("This report is already closed")
        self["users"][user.id] = result

    def end(self) -> None:
        """End the report"""
        if self["end"]:
            raise UserInputError("This report is already closed")
        self["end"] = True
