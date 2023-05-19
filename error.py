from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from response import RespText


class AttendanceError(Exception):
    """Basic error type"""

    pass


class TalkInterrupt(AttendanceError):
    """Raise this when bot requires user to answer question before processing"""

    def __init__(self, resp: "RespText"):
        self.resp = resp


class UserInputError(AttendanceError):
    """User does wrong command"""

    pass


class InternalError(AttendanceError):
    """I did wrong command"""

    pass
