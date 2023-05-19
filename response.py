from typing import Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class RespText:
    """Response oridinary text"""

    text: str
    # json: str = ""


@dataclass
class RespChoice(RespText):
    """Response text with chosable options"""

    choices: list[str] = field(default_factory=list)


def jsonToRespText(data: Any) -> RespText:
    """flatten txt -> RespText"""
    return RespText(jsonToText(data).strip())


def jsonToText(data: Any, indent: int = 0) -> str:
    """Json -> flatten txt"""
    if isinstance(data, (int, str)):
        return str(data)
    elif isinstance(data, datetime):
        return data.strftime("%Y/%m/%d %H:%M")
    elif isinstance(data, dict):
        txt = ""
        for key, value in data.items():
            txt += "\n"
            txt += " " * indent + str(key) + ": "
            txt += jsonToText(value, indent + 2)
        return txt
    elif isinstance(data, (list, tuple)):
        txt = ""
        count = len(data)
        for rank, value in enumerate(data):
            # txt += " " * indent + jsonToRespText(value, indent + 2) + "\n"
            if isinstance(value, (int, str)):
                txt += jsonToText(value, indent + 2)
                count -= 1
                if count:
                    txt += ","
            else:
                txt += " " * indent + str(rank) + ". "
                txt += jsonToText(value, indent + 2)
                txt += "\n"
        return txt
    else:
        raise ValueError
