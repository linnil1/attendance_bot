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
def lineHandle(event):
    logger.debug(str(event))
    line_id = event.source.user_id
    # line_id = "linnil1_admin"
    text = event.message.text
    event = event

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
    app_web = app
    app = attendence_app

    # init for testing
    admin_user = "Udb04a33910ef78f3b66da9da2cfeda89"
    normal_user = "Udb04a33910ef78f3b66da9da2cfeda89"
    app.handle(admin_user, "create team")
    app.handle(admin_user, "Test_team1")
    app.handle(admin_user, "電話")
    t = app.handle(admin_user, "結束")

    import re
    user, admin = re.findall(r"(token-.*)", t.text)
    app.handle(normal_user, "join team")
    app.handle(normal_user, user)
    app.handle(normal_user, "0966")

    app.handle(admin_user, "create report")
    app.handle(admin_user, "repott1")
    app.handle(admin_user, "地點")
    app.handle(admin_user, "結束")

    # end init for testing
    app = app_web
    app.run(host="0.0.0.0", port=settings.port, debug=True)
