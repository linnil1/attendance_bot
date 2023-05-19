from __future__ import annotations
from dataclasses import asdict
from typing import Any, TYPE_CHECKING

from db import db_instance
from question import Question


if TYPE_CHECKING:
    from user import User
    from team import Team


class Report:
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
        questions: [{
           type: str,
           title: str,
           description: str,
           data: json-info
        }]
        users:
            [user-id]:
                answer: json-info
    """

    db = db_instance

    def __init__(self, report_id: str):
        self.id = report_id
        self.report = self.db.get(self.id)

    @classmethod
    def create(cls, name: str, team: "Team", questions: list[Question]) -> Report:
        """Create method"""
        report = Report(cls.db.create("report-"))
        report.report = {
            'end': False,
            "name": name,
            "team": team.id,
            "team_name": team.getName(),
            "users": {},
            "questions": [asdict(q) for q in questions],
        }
        return report

    def __getitem__(self, ind: str) -> Any:
        """Get report dict item"""
        return self.report[ind]

    def __setitem__(self, ind: str, value: Any) -> None:
        """Set report dict item"""
        self.report[ind] = value

    def getName(self) -> str:
        """Get report name"""
        return str(self.report["name"])

    def getTeam(self) -> str:
        """Get report name"""
        return str(self.report["team"])

    def save(self) -> None:
        """Save to DB"""
        assert self.report
        self.db.set(self.id, self.report)

    def addResponse(self, user: "User", result: Any) -> None:
        """User response to report and save here"""
        if self.report['end']:
            raise UserInputError("This report is already closed")
        self.report["users"][user.id] = result

    def end(self) -> None:
        """End the report"""
        if self.report['end']:
            raise UserInputError("This report is already closed")
        self.report["end"] = True
