from __future__ import annotations
from typing import Any, TYPE_CHECKING

from db import db_instance
from error import UserInputError
from question import Question, QType


if TYPE_CHECKING:
    from team import Team
    from report import Report


class User:
    """
    User object.

    The .user method will automatically query DB if not exists.

    Structure:
    ```
    [user-id]:
        id: str
        line: str
        teams:
            [team-id]:
                name: str
                id: str
                role: ["admin", "user"]
        reports:
            [report-id]:
                id: str
                name: str
                end: False
    ```
    """

    db = db_instance

    def __init__(self, line_id: str):
        self.line = line_id
        self.id = "user-" + line_id
        self._user: Any = None

    @classmethod
    def from_id(self, user_id: str) -> User:
        return User(user_id[5:])

    @property
    def user(self) -> Any:
        """Query DB if _user is None and init data if requires creation"""
        if self._user is None:
            self._user = self.db.get(self.id)
        if self._user is None:
            self._user = {
                "id": self.id,
                "line": self.line,
                "profile": {},
                "teams": {},
                "reports": {},
            }
        return self._user

    def updateProfile(self, data: dict[str, str]) -> None:
        """
        Update user profile (with line profile dict as input)

        Example data (LINE format):
        {
          'displayName': 'linnil1',
          'userId': 'Ud',
          'pictureUrl': 'https://profile.line-scdn.net/79',
          'language': 'en'
        }
        """
        self.user['profile'] = data
        self.user['name'] = data['displayName']

    def save(self) -> None:
        """Save to DB"""
        assert self._user
        self.db.set(self.id, self._user)

    def getName(self) -> str:
        """Get user name"""
        return str(self.user.get("name", self.line))

    def join(self, team: "Team", admin: bool) -> None:
        """Join user into team"""
        role = "admin" if admin else "member"
        if team.id in self.user["teams"]:
            joined_team = self.user["teams"][team.id]
            if role in joined_team["role"]:
                raise UserInputError(f"You are already a team {role}")
            joined_team["role"].append(role)
        else:
            self.user["teams"][team.id] = {
                "name": team.getName(),
                "id": team.id,
                "role": [role],
            }

    def generateTeamQuestion(self, has_admin: bool) -> Question:
        """For chooseTeam"""
        buttons: dict[str, str] = {}
        for team_id, team in self.user["teams"].items():
            if has_admin and "admin" not in team["role"]:
                continue
            qid = f"({len(buttons)+1}) {team['name']}".strip()
            buttons[qid] = team_id

        question = Question(
            key="team_id",
            q_type=QType.Choices,
            title="選擇團隊",
            data=buttons,
        )
        return question

    def generateReportQuestion(self, filter_end: bool = False) -> Question:
        """For chooseReport"""
        buttons: dict[str, str] = {}
        for report_id, report in self.user["reports"].items():
            if filter_end and report['end']:
                continue
            qid = f"({len(buttons)+1}) {report['name']}".strip()
            buttons[qid] = report_id

        question = Question(
            key="report_id",
            q_type=QType.Choices,
            title="選擇回報",
            data=buttons,
        )
        return question

    def addReport(self, report: "Report") -> None:
        """Add report for user"""
        self.user["reports"][report.id] = {
            "team": report.getTeam(),
            "name": report.getName(),
            "id": report.id,
            "end": False,
        }

    def endReport(self, report: "Report") -> None:
        """Add report for user"""
        self.user["reports"][report.id]['end'] = True


    def leaveTeam(self, team: "Team") -> None:
        del self.user["teams"][team.id]
        report_ids = []
        for report_id, report in self.user["reports"].items():
            if report["team"] == team.id:
                report_ids.append(report_id)
        for report_id in report_ids:
            del self.user["reports"][report_id]
