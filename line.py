import logging

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction,
)


from command import app as attendence_app
from response import RespText, RespChoice
import settings

app = Flask(__name__)
line_bot_api = LineBotApi(settings.line_token)
handler = WebhookHandler(settings.line_webhook)
logger = logging.getLogger("attendence.line")


@app.route("/callback", methods=["POST"])
async def callback():
    """Flask -> LINE message"""
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    logger.debug("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.debug(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def lineHandle(event: MessageEvent):
    """LINE message -> My Handling"""
    logger.debug(str(event))
    line_id = event.source.user_id
    # line_id = "linnil1_admin"
    text = event.message.text
    # event = event

    resp = attendence_app.handle(line_id, text, event, line_bot_api=line_bot_api)

    if isinstance(resp, RespChoice):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=resp.text,
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=MessageAction(label=choice, text=choice)
                        )
                        for choice in resp.choices
                    ]
                ),
            ),
        )
    elif isinstance(resp, RespText):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=resp.text),
        )


if __name__ == "__main__":
    # init for testing
    # app_web = app
    # app = attendence_app
    # admin_user = settings.line_your_id
    # app.handle(admin_user, "create team")
    # app.handle(admin_user, "Test_team1")
    # app.handle(admin_user, "電話")
    # app.handle(admin_user, "結束")
    # app = app_web
    app.run(host="0.0.0.0", port=settings.port, debug=settings.mode == "test")
