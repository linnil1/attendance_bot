from __future__ import annotations
from typing import TYPE_CHECKING

from error import UserInputError
from question import Question, QType
from base import Base


if TYPE_CHECKING:
    from team import Team
    from report import Report


class User(Base):
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
                team: id
                end: False
    ```
    """

    def __init__(self, line_id: str):
        super().__init__("user-" + line_id)
        self.line = line_id
        self._default = {
            "id": self.id,
            "line": self.line,
            "profile": {},
            "teams": {},
            "reports": {},
        }

    @classmethod
    def from_id(cls, user_id: str) -> User:
        """Get user from app's ID not LINE ID"""
        return User(user_id[5:])

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
        self["profile"] = data
        self["name"] = data["displayName"]

    def getName(self) -> str:
        """Get user name"""
        return str(self.object.get("name", self.line))

    def join(self, team: "Team", admin: bool) -> None:
        """Join user into team"""
        role = "admin" if admin else "member"
        if team.id in self["teams"]:
            joined_team = self["teams"][team.id]
            if role in joined_team["role"]:
                raise UserInputError(f"You are already a team {role}")
            joined_team["role"].append(role)
        else:
            self["teams"][team.id] = {
                "name": team.getName(),
                "id": team.id,
                "role": [role],
            }

    def generateTeamQuestion(self, has_admin: bool) -> Question:
        """For chooseTeam"""
        buttons: dict[str, str] = {}
        for team_id, team in self["teams"].items():
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

    def updateReports(self) -> None:
        """Replace updateUserForReport function"""
        from team import Team

        reports_dict = {}
        for team_id in self["teams"]:
            team = Team(team_id)
            reports = team.listReport()
            for report in reports:
                reports_dict[report["id"]] = {
                    "team": team.id,
                    "team_name": team.getName(),
                    "name": report["name"],
                    "id": report["id"],
                    "end": report["end"],
                }
        self["reports"] = reports_dict
        self.save()

    def generateReportQuestion(self, filter_end: bool = False) -> Question:
        """For chooseReport"""
        self.updateReports()
        buttons: dict[str, str] = {}
        for report_id, report in self["reports"].items():
            if filter_end and report["end"]:
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
        self["reports"][report.id] = {
            "team": report.getTeam(),
            "name": report.getName(),
            "id": report.id,
            "end": False,
        }

    def endReport(self, report: "Report") -> None:
        """End report for user"""
        print(self["reports"])
        self["reports"][report.id]["end"] = True

    def hasAdminReport(self, report_id: str) -> bool:
        """Is the user has the admin of report (related by team)"""
        team_id = self["reports"][report_id]["team"]
        return "admin" in self["teams"][team_id]["role"]

    def leaveTeam(self, team_id: str) -> None:
        """User leave the team"""
        del self["teams"][team_id]
        report_ids = []
        for report_id, report in self["reports"].items():
            if report["team"] == team_id:
                report_ids.append(report_id)
        for report_id in report_ids:
            del self["reports"][report_id]
