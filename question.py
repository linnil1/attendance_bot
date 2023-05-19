from enum import StrEnum, auto
from typing import Any
from dataclasses import dataclass

from error import InternalError, UserInputError
from response import RespText, RespChoice


class QType(StrEnum):
    """Question Type"""

    Choices = auto()
    Short = auto()
    LooseChoices = auto()


@dataclass
class Question:
    """Question Object"""

    q_type: QType
    key: str
    title: str
    description: str = ""
    data: dict[str, str] | None = None

    def toResponse(self) -> RespText:
        """Transfer question to response text or response chocies"""
        text = self.title
        if self.description:
            text += "\n" + self.description

        if self.q_type == QType.Short:
            return RespText(text)
        elif self.q_type == QType.Choices or self.q_type == QType.LooseChoices:
            assert self.data
            return RespChoice(text, choices=list(self.data))
        raise InternalError("Invalid Type")

    def checkResult(self, text: str) -> str:
        """Post-process the user-input"""
        if self.q_type == QType.Choices:
            assert self.data
            if text not in self.data:
                raise UserInputError("Invalid Choices")
            result = self.data[text]
            return result
        if self.q_type == QType.LooseChoices:
            return text
        return text


def createShortQuestion(title: str, description: str = "") -> Question:
    """Short hand for create short question"""
    return Question(
        q_type=QType.Short,
        key=title,
        title=title,
        description=description,
    )
