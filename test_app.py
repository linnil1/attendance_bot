import re
import pytest

from db import db_instance
from error import UserInputError
from command import app
from response import RespChoice
import settings


if settings.mode != "test":
    exit()


def test_app():
    """Test basic usage"""
    db_instance.clear()
    # create Team
    app.handle("linnil1_admin", "create team")
    app.handle("linnil1_admin", "Test_team1")
    app.handle("linnil1_admin", "學號")
    app.handle("linnil1_admin", "姓名")
    # It ignore the same name
    # app.handle("linnil1_admin", "姓名")
    app.handle("linnil1_admin", "電話")
    t = app.handle("linnil1_admin", "結束")
    assert "加入問題" in t.text

    # join team (admin)
    token_user, token_admin = re.findall(r"(token-.*)", t.text)
    app.handle("linnil1_admin2", "join team")
    t = app.handle("linnil1_admin2", token_admin)
    assert "已成功加" in t.text

    # join team (user)
    app.handle("linnil1_user", "join team")
    app.handle("linnil1_user", token_user)
    app.handle("linnil1_user", "123")
    app.handle("linnil1_user", "linnil1_user_name")
    t = app.handle("linnil1_user", "0966")
    assert "已成功加" in t.text

    # join team (multiple user)
    for i in range(10):
        app.handle(f"linnil1_user{i:03d}", "join team")
        app.handle(f"linnil1_user{i:03d}", token_user)
        app.handle(f"linnil1_user{i:03d}", "0966")
        app.handle(f"linnil1_user{i:03d}", f"name{i:03d}")
        t = app.handle(f"linnil1_user{i:03d}", "123")
        assert "已成功加" in t.text

    # list member (admin or not)
    with pytest.raises(UserInputError):
        app.handle("linnil1_user", "list member")
    t = app.handle("linnil1_admin", "list member")
    assert "0. " in t.text
    assert "10. " in t.text

    # create report
    with pytest.raises(UserInputError):
        app.handle("linnil1_user", "create report")
    t = app.handle("linnil1_admin", "create report")
    app.handle("linnil1_admin", "4/26")
    app.handle("linnil1_admin", "地點")
    # app.handle("linnil1_admin", "地點")
    app.handle("linnil1_admin", "喝酒")
    app.handle("linnil1_admin", "22:00後出門嗎")
    t = app.handle("linnil1_admin", "結束")
    assert "回報名稱" in t.text

    # response report
    app.handle("linnil1_user", "response report")
    app.handle("linnil1_user", "not at home")
    app.handle("linnil1_user", "no")
    t = app.handle("linnil1_user", "yes")
    assert "time" in t.text

    # response report (twice)
    app.handle("linnil1_user", "response report")
    app.handle("linnil1_user", "at home")
    app.handle("linnil1_user", "no")
    t = app.handle("linnil1_user", "yes")
    assert "time" in t.text

    # inspect report
    app.handle("linnil1_admin", "inspect report")
    t = app.handle("linnil1_admin", "全部")
    assert "1. " in t.text

    # inspect report (admin)
    t = app.handle("linnil1_admin", "inspect report")
    assert isinstance(t, RespChoice)
    t = app.handle("linnil1_admin", "包含")
    assert isinstance(t, RespChoice)
    app.handle("linnil1_admin", "姓名")
    t = app.handle("linnil1_admin", "linnil1_user_name")
    assert "1. " not in t.text
    assert "0. " in t.text

    # inspect report (user)
    t = app.handle("linnil1_user", "inspect report")
    assert "1. " not in t.text
    assert "0. " in t.text

    # end report
    with pytest.raises(UserInputError):
        app.handle("linnil1_user", "end report")
    t = app.handle("linnil1_admin", "end report")
    assert "已結束" in t.text

    # response to ended report
    with pytest.raises(UserInputError):
        app.handle("linnil1_user", "response report")

    # double join
    app.handle(f"linnil1_user000", "join team")
    app.handle(f"linnil1_user000", token_user)
    app.handle(f"linnil1_user000", "1")
    app.handle(f"linnil1_user000", "2")
    with pytest.raises(UserInputError):
        t = app.handle(f"linnil1_user000", "3")

    # kick member
    app.handle("linnil1_admin", "kick member")
    t = app.handle("linnil1_admin", "4")
    assert "linnil1_user000" in t.text

    # join after kick
    app.handle(f"linnil1_user000", "join team")
    app.handle(f"linnil1_user000", token_user)
    app.handle(f"linnil1_user000", "0966")
    app.handle(f"linnil1_user000", f"name000")
    t = app.handle(f"linnil1_user000", "123")
    assert "已成功加" in t.text

    # leave team
    t = app.handle(f"linnil1_user000", "leave team")
    assert "離開" in t.text


def test_two_team():
    """Test case of two teams and two reports"""
    db_instance.clear()
    # create Team
    app.handle("linnil1_admin", "create team")
    app.handle("linnil1_admin", "Test_team1")
    app.handle("linnil1_admin", "學號")
    t = app.handle("linnil1_admin", "結束")
    app.handle("linnil1_admin", "create team")
    app.handle("linnil1_admin", "Test_team2")
    app.handle("linnil1_admin", "學號")
    app.handle("linnil1_admin", "結束")

    t = app.handle("linnil1_admin", "list member")
    assert isinstance(t, RespChoice)
    assert len(t.choices) == 2
    app.handle("linnil1_admin", t.choices[0])

    # create report
    t = app.handle("linnil1_admin", "create report")
    assert isinstance(t, RespChoice)
    assert len(t.choices) == 2
    app.handle("linnil1_admin", t.choices[0])
    app.handle("linnil1_admin", "4/26")
    app.handle("linnil1_admin", "地點")
    app.handle("linnil1_admin", "結束")
    t = app.handle("linnil1_admin", "create report")
    app.handle("linnil1_admin", t.choices[0])
    app.handle("linnil1_admin", "4/27")
    app.handle("linnil1_admin", "地點")
    t = app.handle("linnil1_admin", "結束")
    assert "回報名稱" in t.text

    # response report
    t = app.handle("linnil1_admin", "response report")
    assert isinstance(t, RespChoice)
    assert len(t.choices) == 2
    app.handle("linnil1_admin", t.choices[0])
    t = app.handle("linnil1_admin", "at home")
    assert "time" in t.text
