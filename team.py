from __future__ import annotations
from typing import Any, TYPE_CHECKING

from base import Base
from error import UserInputError
from question import Question


if TYPE_CHECKING:
    from user import User
    from report import Report


class Token(Base):
    """
    Token mechenism.
    Current use for team joining

    Structure:
      [token-id]:
        action: str
        data: {}
    """

    def __init__(self, token_id: str):
        super().__init__(token_id)

    @classmethod
    def create(cls, action: str, data: Any) -> Token:
        """Create token method"""
        token = cls.newObject(
            "token-",
            {
                "action": action,
                "data": data,
            },
        )
        token.save()
        return token

    @property
    def action(self) -> str:
        """Get action when receive this token"""
        return self["action"]  # type: ignore

    @property
    def data(self) -> Any:
        """Get data of this token"""
        return self["data"]


class Team(Base):
    """
    Team object.

    The .team method will automatically query DB if not exists.

    Structure:
    ```
    [Team-id]:
        name: str
        join_question: list[Question]
        join_admin_token: Token_ID
        join_user_token:  Token_ID
        users:
            [user-id]:
                role: ["admin", "member"],
                id: str,
                line: str,
                question:
                    學號: str,
                    ...
        reports:
            [report-id]:
                id: str,
                name: str,
                end: False,
    """

    # def __init__(self, team_id: str):
    #     super().__init__(team_id)

    @classmethod
    def create(cls, name: str, questions: list[Question]) -> Team:
        """Create team method"""
        team = cls.newObject(
            "team-",
            {
                "name": name,
                "join_questions": questions,  # [asdict(i) for i in questions],
                "users": {},
                "reports": {},
            },
        )
        team["join_admin_token"] = Token.create(
            "add_user_to_team_admin", {"id": team.id}
        ).id
        team["join_user_token"] = Token.create(
            "add_user_to_team_member", {"id": team.id}
        ).id
        return team

    def getName(self) -> str:
        """Get team name"""
        return str(self["name"])

    def join(self, user: "User", admin: bool, member_info: Any = None) -> None:
        """Join user into team"""
        role = "admin" if admin else "member"
        if user.id in self["users"]:
            joined_user = self["users"][user.id]
            if role in joined_user["role"]:
                raise UserInputError("You are already a team {role}")
            joined_user["role"].append(role)
        else:
            self["users"][user.id] = {
                "id": user.id,
                "name": user.getName(),
                "line": user.line,
                "role": [role],
                "question": {},
                "kick": False,
            }

        if role == "member":
            assert member_info
            self["users"][user.id]["question"].update(member_info)

    def generateJoinQuestion(self) -> list[Question]:
        """Create join question object"""
        return [Question(**q) for q in self["join_questions"]]

    def addReport(self, report: "Report") -> None:
        """Add report for the team"""
        self["reports"][report.id] = {
            "name": report.getName(),
            "id": report.id,
            "end": False,
        }

    def endReport(self, report_id: str) -> None:
        """End one of the report"""
        team_report = self["reports"][report_id]
        if team_report["end"]:
            raise UserInputError("This report is already closed")
        team_report["end"] = True

    def listReport(self, filter_end: bool = True) -> list[Any]:
        """List all alive report"""
        reports: list[Any] = self["reports"].values()
        if filter_end:
            reports = [rep for rep in reports if not rep["end"]]
        return reports

    def kickUser(self, user_id: str) -> None:
        """Kick user from team"""
        # Should I mark as kicked
        self["users"][user_id]["kick"] = True

    def listUsers(self) -> list[Any]:
        """List all users"""
        return [u for u in self["users"].values() if not u["kick"]]

    def getUser(self, user_id: str) -> Any:
        """Get User data in team"""
        return self["users"][user_id]
