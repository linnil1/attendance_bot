import logging
import functools
import dataclasses
from typing import Callable, Any

from user import User
from team import Team
from talk import Talk
from report import Report
from error import TalkInterrupt, UserInputError
from response import RespText, RespChoice
from question import Question, QType, createShortQuestion

# can this import be removed from here
from linebot.models import TextSendMessage


@dataclasses.dataclass
class Context:
    """
    Every other things
    """

    event: None  # line
    talk: Talk
    text: str
    line_bot_api: Any

    def getQuestion(self, key: str, prefix: str = "") -> Question:
        key_q = "question-" + prefix + key 
        return Question(**self.talk.get(key_q))

    def ask(self, question: Question, prefix: str = "", clear: bool = False) -> str:
        """
        Ask user additional things inside the command.

        It will save current user's response (state)
        and raise Error to interupt.
        At the next message, it will continue the user's state,
        and continue the command function.
        The message is the answer of the question and will checked and
        returned.
        """
        talk = self.talk
        key_q = "question-" + prefix + question.key
        key_a = "answer-" + prefix + question.key

        answer = talk.get(key_a)
        if answer:
            return str(answer)

        if talk.get(key_q):
            question = self.getQuestion(question.key, prefix)
            result = question.checkResult(self.text)
            talk.set(key_a, result)
            if clear:
                talk.set(key_q, None)
                talk.set(key_a, None)
            talk.save()
            return result

        talk.set(key_q, dataclasses.asdict(question))
        talk.save()
        resp = question.toResponse()
        raise TalkInterrupt(resp)

    def askMany(self, questions: list[Question], prefix: str = "") -> dict[str, str]:
        """Same as ask() but ask more questions at once"""
        result = {}
        for question in questions:
            result[question.key] = self.ask(question, prefix=prefix)
        return result

    def continueAsk(
        self, title: str, description: str, suggestions: list[str]
    ) -> list[str]:
        """Ask question unbilt user say end the message"""
        talk = self.talk
        while True:
            text_list: list[str] = talk.get("continue_text_list", [])
            q = self.ask(
                Question(
                    q_type=QType.LooseChoices,
                    key="continue_text",
                    title=title,
                    description=description,
                    data={i: i for i in [*suggestions, "結束"]},
                ),
                clear=True,
            )
            if q == "結束":
                return text_list
            if q in text_list:
                continue
                # raise UserInputError(f"{q} 已填過")
            text_list.append(q)
            talk.set("continue_text_list", text_list)

    def updateUserProfile(self, user: User) -> None:
        if not self.line_bot_api:
            return
        print("HI", user.line)
        profile = self.line_bot_api.get_profile(user.line)
        user.updateProfile(profile.as_json_dict())

    def notifyReportAll(self, report: Report, text: str) -> None:
        if not self.line_bot_api:
            return
        team = Team(report.getTeam())
        users = team.listUsers()
        line_ids = [user['line'] for user in users]
        self.line_bot_api.multicast(line_ids, TextSendMessage(text=text))


CommandFuncType = Callable[[User, Context], RespText]


class App:
    """
    Main attendence application

    It saves all related command.
    And define how to handle
    """

    logger = logging.getLogger("attendence.app")

    def __init__(self) -> None:
        self.command_keyword: dict[str, CommandFuncType] = {}

    def addCommand(
        self, keywords: list[str]
    ) -> Callable[[CommandFuncType], CommandFuncType]:
        """
        Add the command function to app.

        Use as decorator.
        """

        def wrap(func: CommandFuncType) -> Any:
            for keyword in keywords:
                assert keyword not in self.command_keyword
                self.command_keyword[keyword] = func

            @functools.wraps(func)
            def wrap2(*arg: Any, **kwargs: Any) -> RespText:
                return func(*arg, **kwargs)

            return wrap2

        return wrap

    def handle(self, line_id: str, text: str, event: Any = None, line_bot_api: Any = None) -> RespText:
        """
        Define how to handle the message:
        1. Continue talk state (if saved)
        2. trigger command by text
        3. handle error message
        """
        self.logger.debug(f"{line_id}: {text}")
        user = User(line_id)
        talk = Talk(line_id)
        context = Context(
            event=event,
            talk=talk,
            text=text,
            line_bot_api=line_bot_api,
        )
        try:
            # continue talk state
            if talk:
                keyword = talk.keyword
            # Select command user want to trigger
            else:
                keyword = text

            # keyword trigger
            if keyword in self.command_keyword:
                talk.set("keyword", keyword)
                result = self.command_keyword[keyword](user, context)
                # success command, clear key
                context.talk.clear()
                self.logger.debug(f"bot: {result}")
                return result
            # error
            else:
                return RespText("Error")
        except TalkInterrupt as e:
            self.logger.debug(f"bot: ask {e.resp}")
            return e.resp
        # except UserInputError as e:
        #     self.logger.debug(f"Error: {e.args[0]}")
        #     context.talk.clear()
        #     return RespText(e.args[0])
