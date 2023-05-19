from __future__ import annotations
from typing import Any, TYPE_CHECKING
from dataclasses import asdict

from db import db_instance
from error import UserInputError
from question import Question


if TYPE_CHECKING:
    from user import User
    from report import Report


class Token:
    """
    Token mechenism.
    Current use for team joining

    Structure:
      [token-id]:
        action: str
        data: {}
    """
    db = db_instance

    def __init__(self, token_id: str):
        self.id = token_id
        self.token = self.db.get(self.id) or {}

    def __bool__(self) -> bool:
        """Is this token exists"""
        return bool(self.token)

    @classmethod
    def create(cls, action: str, data: Any) -> Token:
        """Create token method"""
        token = Token(cls.db.create("token-"))
        token.token = {
            "action": action,
            "data": data,
        }
        cls.db.set(token.id, token.token)
        return token

    @property
    def action(self) -> str:
        """Get action when receive this token"""
        return self.token["action"]  # type: ignore

    @property
    def data(self) -> Any:
        """Get data of this token"""
        return self.token["data"]


class Team:
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

    db = db_instance

    def __init__(self, team_id: str):
        self.id = team_id
        self.team = self.db.get(self.id)

    @classmethod
    def create(cls, name: str, questions: list[Question]) -> Team:
        """Create team method"""
        team = Team(cls.db.create("team-"))
        # asdict(createShortQuestion("學號", "你的學號")),
        team.team = {
            "id": team.id,
            "name": name,
            "join_admin_token": Token.create(
                "add_user_to_team_admin", {"id": team.id}
            ).id,
            "join_user_token": Token.create(
                "add_user_to_team_member", {"id": team.id}
            ).id,
            "join_questions": [asdict(i) for i in questions],
            "users": {},
            "reports": {},
        }
        return team

    def __getitem__(self, ind: str) -> Any:
        """getter to team object"""
        return self.team[ind]

    def __setitem__(self, ind: str, value: Any) -> None:
        """setter to team object"""
        self.team[ind] = value

    def getName(self) -> str:
        """Get team name"""
        return str(self.team["name"])

    def save(self) -> None:
        """Save to DB"""
        assert self.team
        self.db.set(self.id, self.team)

    def join(self, user: "User", admin: bool, member_info: Any = None) -> None:
        """Join user into team"""
        role = "admin" if admin else "member"
        if user.id in self.team["users"]:
            joined_user = self.team["users"][user.id]
            if role in joined_user["role"]:
                raise UserInputError("You are already a team {role}")
            joined_user["role"].append(role)
        else:
            self.team["users"][user.id] = {
                "id": user.id,
                "name": user.getName(),
                "line": user.line,
                "role": [role],
                "question": {},
                "kick": False,
            }

        if role == "member":
            assert member_info
            self.team["users"][user.id]["question"].update(member_info)

    def generateJoinQuestion(self) -> list[Question]:
        """Create join question object"""
        return [Question(**q) for q in self.team["join_questions"]]

    def addReport(self, report: "Report") -> None:
        """Add report for the team"""
        self.team["reports"][report.id] = {
            "name": report.getName(),
            "id": report.id,
            "end": False,
        }

    def kickUser(self, user_id: str) -> None:
        """Kick user from team"""
        # Should I mark as kicked
        self.team["users"][user_id]["kick"] = True

    def listUsers(self) -> list[Any]:
        """List all users"""
        return [u for u in self.team["users"].values() if not u["kick"]]

    def getUser(self, user_id: str) -> Any:
        """Get User data in team"""
        return self["users"][user_id]
