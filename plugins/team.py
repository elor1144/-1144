from nonebot import on_command
from nonebot.adapters.qq import Bot, MessageSegment, GroupMessageEvent
import json
import os

# ===== 数据存取 =====
BASE = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE, "team_data.json")
MAX_MEMBER = 8
# 想指定某QQ为管理员就填这里，例如 {"123456789"}
ADMIN_QQS = set()


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"teams": {}, "history": []}


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


data = load_data()


def is_admin(event: GroupMessageEvent) -> bool:
    return event.sender.role in ("owner", "admin") or event.get_user_id() in ADMIN_QQS


def get_team(tid):
    return data["teams"].get(str(tid))


def new_team(tid):
    data["teams"][str(tid)] = {"members": [], "remark": "", "active": True, "name": ""}
    save_data()


def archive_team(tid):
    t = get_team(tid)
    if not t:
        return
    rec = {
        "team_id": tid,
        "remark": t.get("remark", ""),
        "name": t.get("name", ""),
        "members": list(t["members"]),
    }
    data.setdefault("history", [])
    data["history"].append(rec)
    if len(data["history"]) > 50:
        data["history"] = data["history"][-50:]
    save_data()


def team_label(t):
    return t.get("remark") or t.get("name") or ""


# ===== 1. 丹丹组队1 / 丹丹组队2 =====
@on_command("丹丹组队1").handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await create_team(event, 1)


@on_command("丹丹组队2").handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await create_team(event, 2)


async def create_team(event: GroupMessageEvent, tid):
    if not is_admin(event):
        await on_command("丹丹组队1").finish("只有管理员才能开队哦～")
    t = get_team(tid)
    if t and t["active"]:
        await on_command("丹丹组队1").finish(f"第{tid}队已经在开了，别重复创建～")
    new_team(tid)
    await on_command("丹丹组队1").send(
        f"创建成功！扣一加入组队\n第{tid}队已开启，最多两队并存～"
    )


# ===== 2. 扣 1 / 扣 2（带不带空格都行）=====
@on_command("扣1").handle()
@on_command("扣 1").handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await join_team(event, 1)


@on_command("扣2").handle()
@on_command("扣 2").handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await join_team(event, 2)


async def join_team(event: GroupMessageEvent, tid):
    t = get_team(tid)
    if not t or not t["active"]:
        await on_command("扣1").finish(f"第{tid}队还没开，先让管理员发「丹丹组队{tid}」～")
    uid = event.get_user_id()
    if uid in t["members"]:
        await on_command("扣1").finish(f"你已经在本队啦，当前 {len(t['members'])} 人")
    t["members"].append(uid)
    save_data()
    if len(t["members"]) >= MAX_MEMBER:
        ats = "".join(str(MessageSegment.mention_qq(q)) for q in t["members"])
        archive_team(tid)
        await on_command("扣1").send(f"加入成功！当前人数{len(t['members'])}人\n已满员！\n{ats}")
    else:
        await on_command("扣1").send(f"加入成功！当前人数{len(t['members'])}人")


# ===== 3. 组队退出1 / 组队退出2 =====
@on_command("组队退出1").handle()
@on_command("组队退出2").handle()
async def _(bot: Bot, event: GroupMessageEvent):
    raw = event.get_message().extract_plain_text()
    tid = 1 if "1" in raw else 2
    t = get_team(tid)
    if not t or not t["active"]:
        await on_command("组队退出1").finish(f"第{tid}队没开着呢～")
    uid = event.get_user_id()
    if uid in t["members"]:
        t["members"].remove(uid)
        save_data()
        await on_command("组队退出1").send(f"退出成功！第{tid}队当前人数{len(t['members'])}人")
    else:
        await on_command("组队退出1").send(f"你不在第{tid}队里哦～")


# ===== 4. 组队开始1 / 组队开始2（存档）=====
@on_command("组队开始1").handle()
@on_command("组队开始2").handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not is_admin(event):
        await on_command("组队开始1").finish("只有管理员才能存档哦～")
    raw = event.get_message().extract_plain_text()
    tid = 1 if "1" in raw else 2
    archive_team(tid)
    await on_command("组队开始1").send("组队已开始，已保存记录")


# ===== 5. 组队结束1 / 组队结束2 =====
@on_command("组队结束1").handle()
@on_command("组队结束2").handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not is_admin(event):
        await on_command("组队结束1").finish("只有管理员才能结束组队～")
    raw = event.get_message().extract_plain_text()
    tid = 1 if "1" in raw else 2
    t = get_team(tid)
    if not t:
        await on_command("组队结束1").finish(f"第{tid}队本来就没开～")
    t["active"] = False
    save_data()
    await on_command("组队结束1").send(f"第{tid}队已停止组队")


# ===== 6. 组队备注1 / 组队备注2 + 名称 =====
@on_command("组队备注1").handle()
@on_command("组队备注2").handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not is_admin(event):
        await on_command("组队备注1").finish("只有管理员才能改备注～")
    raw = event.get_message().extract_plain_text()
    tid = 1 if "1" in raw else 2
    name = (
        raw.replace("组队备注1", "")
        .replace("组队备注2", "")
        .replace("组队备注", "")
        .strip()
    )
    t = get_team(tid)
    if not t:
        await on_command("组队备注1").finish(f"第{tid}队还没开～")
    t["remark"] = name
    t["name"] = name
    save_data()
    await on_command("组队备注1").send(f"组队{tid}备注成功，第{tid}队名称改为「{name}」")


# ===== 7. 组队计数1 / 组队计数2 =====
@on_command("组队计数1").handle()
@on_command("组队计数2").handle()
async def _(bot: Bot, event: GroupMessageEvent):
    raw = event.get_message().extract_plain_text()
    tid = 1 if "1" in raw else 2
    t = get_team(tid)
    if not t or not t["active"]:
        await on_command("组队计数1").finish(f"第{tid}队没开着呢～")
    members = t["members"]
    label = team_label(t) or f"第{tid}队"
    if not members:
        await on_command("组队计数1").send(f"{label} 已有 0 人")
        return
    lines = [f"{label} 已有 {len(members)} 人："]
    for i, q in enumerate(members, 1):
        lines.append(f"{i}. {q}")
    await on_command("组队计数1").send("\n".join(lines))


# ===== 8. 组队艾特1 / 组队艾特2 =====
@on_command("组队艾特1").handle()
@on_command("组队艾特2").handle()
async def _(bot: Bot, event: GroupMessageEvent):
    raw = event.get_message().extract_plain_text()
    tid = 1 if "1" in raw else 2
    t = get_team(tid)
    if not t or not t["active"]:
        await on_command("组队艾特1").finish(f"第{tid}队没开着呢～")
    members = t["members"]
    label = team_label(t) or f"第{tid}队"
    if not members:
        await on_command("组队艾特1").send(f"{label} 暂时没人～")
        return
    ats = "".join(str(MessageSegment.mention_qq(q)) for q in members)
    diff = MAX_MEMBER - len(members)
    if diff > 0:
        await on_command("组队艾特1").send(f"{label}名单：\n{ats}\n(艾特完成 还差{diff}人满人)")
    else:
        await on_command("组队艾特1").send(f"{label}名单：\n{ats}")


# ===== 9. 组队历史 =====
@on_command("组队历史").handle()
async def _(bot: Bot, event: GroupMessageEvent):
    hist = data.get("history", [])
    if not hist:
        await on_command("组队历史").send("📜 还没有任何组队记录哦～")
        return
    lines = ["📜 最近组队记录（含备注名）："]
    for h in hist[-10:]:
        tid = h.get("team_id")
        name = h.get("remark") or h.get("name") or f"第{tid}队"
        lines.append(f"· {name}（{len(h.get('members', []))}人）")
    await on_command("组队历史").send("\n".join(lines))


# ===== 10. 丹丹菜单 =====
@on_command("丹丹菜单").handle()
async def _(bot: Bot, event: GroupMessageEvent):
    msg = (
        "🤖 组队助手 菜单\n"
        "━━━━━━━━\n"
        "【开队】丹丹组队1 / 丹丹组队2（管理员）\n"
        "【加入】扣 1 / 扣 2\n"
        "【退出】组队退出1 / 组队退出2\n"
        "【存档】组队开始1 / 组队开始2（管理员）\n"
        "【结束】组队结束1 / 组队结束2（管理员）\n"
        "【备注】组队备注1 / 组队备注2 + 名称（管理员）\n"
        "【计数】组队计数1 / 组队计数2\n"
        "【艾特】组队艾特1 / 组队艾特2\n"
        "【历史】组队历史\n"
        "━━━━━━━━\n"
        "满8人自动艾特+存档"
    )
    await on_command("丹丹菜单").send(msg)
