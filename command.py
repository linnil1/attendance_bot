from typing import Callable, Any
from datetime import datetime

from user import User
from team import Team, Token
from error import UserInputError
from report import Report
from history import History
from question import Question, QType, createShortQuestion
from response import RespText, jsonToRespText
from attendence import Context, App


app = App()


def chooseTeam(context: Context, user: User, has_admin: bool = True) -> str:
    """Ask which user's team the user want to choose"""
    question = user.generateTeamQuestion(has_admin=has_admin)
    if not question.data:
        raise UserInputError("你在你的團隊中都沒有管理員權限")
        # raise UserInputError("You don't have admin in all of your team")
    if len(question.data) == 1:
        return next(iter(question.data.values()))
    return context.ask(question)


def chooseReport(context: Context, user: User, filter_end: bool = True) -> str:
    """Ask which user's report the user want to choose"""
    question = user.generateReportQuestion(filter_end=filter_end)
    if not question.data:
        raise UserInputError("目前在你的團隊中都沒有需要回報的")
        # raise UserInputError("You don't have any report in all of your team")
    if len(question.data) == 1:
        return next(iter(question.data.values()))
    return context.ask(question)


def userJoinTeam(user: User, team: Team, admin: bool, context: Context) -> None:
    """Join user to team and add team to user"""
    # team
    member_info = None
    if not admin:
        member_info = context.askMany(team.generateJoinQuestion(), prefix="xxx-")
    user.join(team, admin=admin)
    context.updateUserProfile(user)
    user.save()
    team.block()
    team.join(user, admin=admin, member_info=member_info)
    team.save()


@app.addCommand(keywords=["create team", "新增團隊"])
def createTeam(user: User, context: Context) -> RespText:
    """Command: Create Team"""
    name = context.ask(createShortQuestion("團隊名稱"))
    text_list = context.continueAsk("項目", "請輸入加入團隊所需填寫的項目 (可自行填寫) ", ["學號", "姓名", "電話"])
    questions = [createShortQuestion(text) for text in text_list]
    team = Team.create(name, questions)
    team.save()
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
    """Command: Join to Team"""
    token_str = context.ask(createShortQuestion("請輸入token"))
    token = Token(token_str)
    if not token:
        raise UserInputError("Token 不正確")
        # raise UserInputError("Invalid Token")

    if token.action == "add_user_to_team_admin":
        admin = True
    elif token.action == "add_user_to_team_member":
        admin = False
    else:
        raise UserInputError("Token 不正確")
        # raise UserInputError("Invalid Token")

    team = Team(token.data["id"])
    userJoinTeam(user, team, admin=admin, context=context)
    data = {
        "已成功加入": team.getName(),
        "角色": "管理員" if admin else "一般使用者",
        "姓名": user.getName(),
    }
    if not admin:
        data.update(team.getUser(user.id)["question"])
    return jsonToRespText(data)


@app.addCommand(keywords=["list member", "列出團隊成員"])
def listMember(user: User, context: Context) -> RespText:
    """Command(Admin): List team member"""
    team_id = chooseTeam(context, user, has_admin=True)
    users = Team(team_id).listUsers()
    users = [
        {
            "姓名": u["name"],
            "權限": u["role"],
            "加入資料": u["question"],
        }
        for u in users
    ]
    return jsonToRespText(users)


@app.addCommand(keywords=["kick member", "踢除隊員"])
def kickMember(user: User, context: Context) -> RespText:
    """Command(Admin): Kick team member"""
    team_id = chooseTeam(context, user, has_admin=True)
    team = Team(team_id)
    users = team.listUsers()
    uid = context.ask(
        Question(
            q_type=QType.Short,
            key="user_id",
            title="請輸入編號",
            description="\n".join(f"{i}. {u['name']}" for i, u in enumerate(users)),
            data=users,  # type: ignore
        )
    )
    users = context.getQuestion("user_id").data  # type: ignore
    try:
        int(uid)
        if not 1 <= int(uid) <= len(users):
            raise UserInputError("錯誤編號")
            # raise UserInputError("Invalid ID")
    except ValueError:
        raise UserInputError("錯誤編號")
        # raise UserInputError("Invalid ID")

    user_id = users[int(uid) - 1]["id"]
    team.kickUser(user_id)
    team.save()
    kicked_user = User.from_id(user_id)
    kicked_user.leaveTeam(team.id)
    kicked_user.save()
    return jsonToRespText({"踢除": User(user_id).getName()})


@app.addCommand(keywords=["leave team", "離開團隊"])
def leaveTeam(user: User, context: Context) -> RespText:
    """Command: leave team"""
    team_id = chooseTeam(context, user, has_admin=False)
    team = Team(team_id)
    team.kickUser(user.id)
    team.save()
    user.leaveTeam(team.id)
    user.save()
    return jsonToRespText({"離開": team.getName()})


def updateUserForReport(team: Team, report: Report, status: str) -> None:
    """
    Deprecated: When memeber needs, fetch from team
    Add/end report to all memebers
    """
    for info in team.listUsers():
        user = User(info["line"])
        if status == "start":
            user.addReport(report)
        elif status == "end":
            user.endReport(report)
        else:
            raise ValueError()
        user.save()


@app.addCommand(keywords=["create report", "新增回報"])
def createReport(user: User, context: Context) -> RespText:
    """Command(Admin): Create new report for team"""
    team_id = chooseTeam(context, user, has_admin=True)
    name = context.ask(createShortQuestion("回報標題"))
    text_list = context.continueAsk("項目", "請輸入回報所需填寫的項目 (可自行填寫) ", ["地點", "喝酒"])
    questions = [createShortQuestion(text) for text in text_list]
    team = Team(team_id)
    report = Report.create(name=name, team=team, questions=questions)
    report.save()
    team.addReport(report)
    team.save()
    # updateUserForReport(team, report, status="start")
    context.notifyReportAll(report, f"{report['team_name']} ㄉ {report.getName()} 已開始")
    return jsonToRespText(
        {
            "回報名稱": report["name"],
            "回報問題": text_list,
        }
    )


@app.addCommand(keywords=["response report", "回報"])
def responseReport(user: User, context: Context) -> RespText:
    """Command: User response the report"""
    report_id = chooseReport(context, user)

    report = Report(report_id)
    questions = report.generateQuestion()
    result = context.askMany(questions, prefix="xxx-")
    result["time"] = datetime.now()  # type: ignore

    history = History(report.id, user.id)
    history.addResponse(result)
    history.save()
    report.block()
    report.addResponse(user.id, result)
    report.save()
    return jsonToRespText(
        {
            "回報": report["name"],
            **result,
        }
    )


@app.addCommand(keywords=["inspect report", "檢視回報"])
def inspectReport(user: User, context: Context) -> RespText:
    """Command: Inspect the report"""
    report_id = chooseReport(context, user, filter_end=False)
    filter_func: Callable[[Any], bool] = lambda i: True
    if user.hasAdminReport(report_id):
        filter_type = context.ask(
            Question(
                q_type=QType.Choices,
                key="filter",
                title="篩選機制",
                data={"全部": "all", "包含": "include", "排除": "exclude"},
            )
        )
        if filter_type == "all":
            pass
        elif filter_type == "include" or filter_type == "exclude":
            report = Report(report_id)
            team = Team(report.getTeam())
            item = context.ask(
                Question(
                    q_type=QType.Choices,
                    key="item",
                    title="對象",
                    data={
                        q.title: q.title
                        for q in (
                            *report.generateQuestion(),
                            *team.generateJoinQuestion(),
                        )
                    },
                )
            )
            value = context.ask(createShortQuestion("值"))
            if filter_type == "include":
                filter_func = lambda u: value in u.get(item, "")
            else:
                filter_func = lambda u: value not in u.get(item, "")

    # join: memeber info + report answer
    report = Report(report_id)
    team = Team(report.getTeam())
    if user.hasAdminReport(report_id):
        users_id = set(report["users"]) | set(i['id'] for i in team.listUsers())
    else:
        # user inspect itself
        users_id = set([user.id])
    users = [
        {
            "line": team["users"][user_id]["name"],
            **team.getMemberInfo(user_id),
            **report.getMemberResponse(user_id),
        }
        for user_id in users_id
    ]
    users = [u for u in users if filter_func(u)]
    users = sorted(users, key=lambda i: i["line"])  # type: ignore
    return jsonToRespText(list(users))


@app.addCommand(keywords=["end report", "結束回報"])
def endReport(user: User, context: Context) -> RespText:
    """Command(Admin):  Stop user from responsing to report"""
    report_id = chooseReport(context, user)
    if not user.hasAdminReport(report_id):
        raise UserInputError("You are not admin of the report")
    report = Report(report_id)
    report.end()
    report.save()

    team = Team(report.getTeam())
    team.endReport(report.id)
    team.save()
    # updateUserForReport(team, report, status="end")
    context.notifyReportAll(report, f"{report['team_name']} ㄉ {report.getName()} 已結束")
    return RespText(f"{report.getName()} 已結束")
