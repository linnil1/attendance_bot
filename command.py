from user import User
from team import Team, Token
from error import UserInputError
from report import Report
from history import History
from question import Question, QType, createShortQuestion
from response import RespText, RespChoice, jsonToRespText
from attendence import Context, App


app = App()


def chooseTeam(context: Context, user: User, has_admin: bool = True) -> str:
    question = user.generateTeamQuestion(has_admin=has_admin)
    if not question.data:
        raise UserInputError("你在你的團隊中都沒有管理員權限")
        # raise UserInputError("You don't have admin in all of your team")
    if len(question.data) == 1:
        return next(iter(question.data.values()))
    return context.ask(question)


def chooseReport(context: Context, user: User, filter_end: bool = True) -> str:
    question = user.generateReportQuestion(filter_end=filter_end)
    if not question.data:
        raise UserInputError("目前在你的團隊中都沒有需要回報的")
        # raise UserInputError("You don't have any report in all of your team")
    if len(question.data) == 1:
        return next(iter(question.data.values()))
    return context.ask(question)


def userJoinTeam(user: User, team: Team, admin: bool, context: Context) -> None:
    # team
    member_info = None
    if not admin:
        member_info = context.askMany(team.generateJoinQuestion(), prefix="xxx-")
    user.join(team, admin=admin)
    context.updateUserProfile(user)
    team.join(user, admin=admin, member_info=member_info)
    team.save()
    user.save()


@app.addCommand(keywords=["create team", "新增團隊"])
def createTeam(user: User, context: Context) -> RespText:
    name = context.ask(createShortQuestion("團隊名稱"))
    text_list = context.continueAsk("項目", "請輸入加入團隊所需填寫的項目 (可自行填寫) ", ["學號", "姓名", "電話"])
    questions = [createShortQuestion(text) for text in text_list]
    team = Team.create(name, questions)
    userJoinTeam(user, team, admin=True, context=context)
    return jsonToRespText(
        {
            "名稱": team.getName(),
            "加入token": team["join_user_token"],
            "加入token(for 管理者)": team["join_admin_token"],
            "加入問題": [i["title"] for i in team["join_questions"]],
        }
    )


@app.addCommand(keywords=["join team", "加入團隊"])
def joinTeam(user: User, context: Context) -> RespText:
    token_str = context.ask(createShortQuestion("請輸入token"))
    token = Token(token_str)
    if not token:
        raise UserInputError("Token 不正確")
        # raise UserInputError("Invalid Token")

    team = Team(token.data["id"])
    # TODO: Lock
    if token.action == "add_user_to_team_admin":
        admin = True
    elif token.action == "add_user_to_team_member":
        admin = False
    else:
        raise UserInputError("Token 不正確")
        # raise UserInputError("Invalid Token")

    userJoinTeam(user, team, admin=admin, context=context)
    data = {
        "已成功加入": team.getName(),
        "角色": "管理員" if admin else "一般使用者",
        '姓名': user.getName(),
    }
    if not admin:
        data.update(team.getUser(user.id)["question"])
    return jsonToRespText(data)


@app.addCommand(keywords=["list member", "列出團隊成員"])
def listMember(user: User, context: Context) -> RespText:
    team_id = chooseTeam(context, user, has_admin=True)
    users = Team(team_id).listUsers()
    users = [{
        '姓名': u['name'],
        '權限': u['role'],
        '加入資料': u['question'],
    } for u in users]
    return jsonToRespText(users)


@app.addCommand(keywords=["kick member", "踢除隊員"])
def kickMember(user: User, context: Context) -> RespText:
    team_id = chooseTeam(context, user, has_admin=True)
    team = Team(team_id)
    users = team.listUsers()
    uid = context.ask(Question(
        q_type=QType.Short,
        key="user_id",
        title="請輸入編號",
        description="\n".join(f"{i}. {u['name']}" for i, u in enumerate(users)),
        data=users,  # type: ignore
    ))
    users = context.getQuestion("user_id").data  # type: ignore
    try:
        int(uid)
        if not 1 <= int(uid) <= len(users):
            raise UserInputError("錯誤編號")
            # raise UserInputError("Invalid ID")
    except ValueError: 
        raise UserInputError("錯誤編號")
        # raise UserInputError("Invalid ID")

    user_id = users[int(uid) - 1]['id']
    team.kickUser(user_id)
    team.save()
    kicked_user = User.from_id(user_id)
    kicked_user.leaveTeam(team)
    kicked_user.save()
    return jsonToRespText({"kick": User(user_id).getName()})


@app.addCommand(keywords=["create report", "新增回報"])
def createReport(user: User, context: Context) -> RespText:
    team_id = chooseTeam(context, user, has_admin=True)
    name = context.ask(createShortQuestion("回報標題"))
    text_list = context.continueAsk("項目", "請輸入回報所需填寫的項目 (可自行填寫) ", ["地點", "喝酒"])
    questions = [createShortQuestion(text) for text in text_list]
    team = Team(team_id)
    report = Report.create(name=name, team=team, questions=questions)
    report.save()

    team.addReport(report)
    team.save()

    # Add report to all memebers
    for info in team.listUsers():
        user = User(info["line"])
        user.addReport(report)
        user.save()

    context.notifyReportAll(report, f"{report['team_name']} ㄉ {report.getName()} 已開始")
    return jsonToRespText(
        {
            "回報名稱": report["name"],
            "回報問題": text_list,
        }
    )


@app.addCommand(keywords=["response report", "回報"])
def responseReport(user: User, context: Context) -> RespText:
    report_id = chooseReport(context, user)
    report = Report(report_id)

    questions = [Question(**q) for q in report["questions"]]
    result = context.askMany(questions, prefix="xxx-")
    history = History(report.id, user.id)
    history.addResponse(result)
    history.save()
    report.addResponse(user, result)
    report.save()
    print(result)
    return jsonToRespText(
        {
            "回報": report["name"],
            **result,
        }
    )


@app.addCommand(keywords=["inspect report", "檢視回報"])
def inspectReport(user: User, context: Context) -> RespText:
    report_id = chooseReport(context, user, filter_end=False)
    filter_type = context.ask(
        Question(
            q_type=QType.Choices,
            key="filter",
            title="篩選機制",
            data={"全部": "all", "包含": "include", "排除": "exclude"},
        )
    )
    report = Report(report_id)
    team = Team(report.getTeam())

    # join: memeber info + report answer
    users = [
        {'name': team["users"][user_id]['name'], **report["users"].get(user_id, {})}
        for user_id in (set(report["users"]) | set(team["users"]))
    ]
    if filter_type == "all":
        pass
    elif filter_type == "include" or filter_type == "exclude":
        item = context.ask(
            Question(
                q_type=QType.Choices,
                key="item",
                title="對象",
                data={q["title"]: q["title"] for q in report["questions"]},
            )
        )
        value = context.ask(createShortQuestion("值"))
        if filter_type == "include":
            users = [u for u in users if value in u.get(item, "")]
        else:
            users = [u for u in users if value not in u.get(item, "")]

    users = sorted(users, key=lambda i: i['name'])
    return jsonToRespText(list(users))


@app.addCommand(keywords=["end report", "結束回報"])
def endReport(user: User, context: Context) -> RespText:
    report_id = chooseReport(context, user)
    report = Report(report_id)
    report.end()
    report.save()
    context.notifyReportAll(report, f"{report['team_name']} ㄉ {report.getName()} 已結束")

    team = Team(report.getTeam())
    for u in team.listUsers():
        user  = User.from_id(u['id'])
        print(user.user)
        user.endReport(report)
        user.save()
    # TODO: notify user
    return RespText(f"{report.getName()} 已結束")


if __name__ == "__main__":
    """
    Test code
    """
    import settings
    if settings.mode != "test":
        exit()

    app.handle("linnil1_admin", "create team")
    app.handle("linnil1_admin", "Test_team1")
    app.handle("linnil1_admin", "學號")
    app.handle("linnil1_admin", "姓名")
    try:
        app.handle("linnil1_admin", "姓名")
    except:
        pass
    app.handle("linnil1_admin", "電話")
    app.handle("linnil1_admin", "Test_q1")
    t = app.handle("linnil1_admin", "結束")

    import re
    user, admin = re.findall(r"(token-.*)", t.text)
    app.handle("linnil1_admin2", "join team")
    app.handle("linnil1_admin2", admin).text

    app.handle("linnil1_user", "join team")
    app.handle("linnil1_user", user)
    app.handle("linnil1_user", "0966")
    app.handle("linnil1_user", "linnil1_user_name")
    app.handle("linnil1_user", "123")
    app.handle("linnil1_user", "Test_select1").text

    # print(app.handle("linnil1_user", "list member"))
    t = app.handle("linnil1_admin", "list member")
    # assert isinstance(t, RespChoice)
    # app.handle("linnil1_admin", t.choices[0]).text

    t = app.handle("linnil1_admin", "create report")
    # assert isinstance(t, RespChoice)
    # app.handle("linnil1_admin", t.choices[0])
    app.handle("linnil1_admin", "4/26")
    app.handle("linnil1_admin", "地點")
    app.handle("linnil1_admin", "喝酒")
    app.handle("linnil1_admin", "22:00後出門嗎")
    app.handle("linnil1_admin", "結束").text

    t = app.handle("linnil1_user", "response report")
    # assert isinstance(t, RespChoice)
    # app.handle("linnil1_user", t.choices[0])
    app.handle("linnil1_user", "at home")
    app.handle("linnil1_user", "no")
    app.handle("linnil1_user", "yes").text

    t = app.handle("linnil1_user", "inspect report")
    # assert isinstance(t, RespChoice)
    # app.handle("linnil1_user", t.choices[0])
    app.handle("linnil1_user", "全部").text

    t = app.handle("linnil1_user", "inspect report")
    # assert isinstance(t, RespChoice)
    # app.handle("linnil1_user", t.choices[0])
    app.handle("linnil1_user", "包含")
    app.handle("linnil1_user", "地點")
    print(app.handle("linnil1_user", "at home").text)
    exit()

    # t = app.handle("linnil1_admin", "kick member")
    # assert isinstance(t, RespChoice)
    # app.handle("linnil1_admin", t.choices[0]).text
    # print(app.handle("linnil1_admin", "2").text)


    t = app.handle("linnil1_admin", "end report")
    # assert isinstance(t, RespChoice)
    # app.handle("linnil1_admin", t.choices[0]).text

    t = app.handle("linnil1_admin", "end report")
