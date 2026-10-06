from nonebot import on_message
from nonebot.adapters.qq import Bot, MessageSegment, Event
import json, os

BASE = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE, "team_data.json")
MAX_MEMBER = 8
ADMIN_QQS = {"2963592929", "3166683679", "385697093"}  # 管理员QQ号，多个用逗号加

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"teams": {}, "history": []}

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

data = load_data()

def is_admin(event):
    return str(event.get_user_id()) in ADMIN_QQS

def get_team(tid):
    return data["teams"].get(str(tid))

def new_team(tid):
    data["teams"][str(tid)] = {"members": [], "remark": "", "active": True, "name": ""}
    save_data(data)

def archive_team(tid):
    t = get_team(tid)
    if not t:
        return
    data.setdefault("history", [])
    data["history"].append({"team_id": tid, "remark": t.get("remark",""), "name": t.get("name",""), "members": list(t["members"])})
    if len(data["history"]) > 50:
        data["history"] = data["history"][-50:]
    save_data(data)

def label(t):
    return t.get("remark") or t.get("name") or ""

@on_message(priority=1).handle()
async def handle(bot: Bot, event: Event):
    text = event.get_message().extract_plain_text().strip().strip("！!。.，,~～ ")
    if not text:
        return
    if text not in (
        "丹丹菜单","丹丹组队1","丹丹组队2","1","2",
        "组队退出1","组队退出2","组队开始1","组队开始2",
        "组队结束1","组队结束2","组队计数1","组队计数2",
        "组队艾特1","组队艾特2","组队历史"
    ) and not text.startswith("组队备注"):
        return
    uid = str(event.get_user_id())

    if text == "丹丹菜单":
        await bot.send(event,
            "🤖 组队助手 菜单\n━━━━━━━━\n"
            "【开队】丹丹组队1 / 丹丹组队2（管理员）\n"
            "【加入】直接发 1 / 2\n"
            "【退出】组队退出1 / 组队退出2\n"
            "【存档】组队开始1 / 组队开始2（管理员）\n"
            "【结束】组队结束1 / 组队结束2（管理员）\n"
            "【备注】组队备注1 / 组队备注2 + 名称（管理员）\n"
            "【计数】组队计数1 / 组队计数2\n"
            "【艾特】组队艾特1 / 组队艾特2\n"
            "【历史】组队历史\n━━━━━━━━\n满8人自动艾特+存档")
        return

    if text in ("丹丹组队1","丹丹组队2"):
        if not is_admin(event):
            await bot.send(event, "只有管理员才能开队哦～"); return
        tid = 1 if text.endswith("1") else 2
        t = get_team(tid)
        if t and t["active"]:
            await bot.send(event, f"第{tid}队已经在开了～"); return
        new_team(tid)
        await bot.send(event, f"第{tid}队已开启，最多两队并存～")
        return

    if text == "1":
        tid = 1
    elif text == "2":
        tid = 2
    else:
        tid = 0
    if tid:
        t = get_team(tid)
        if not t or not t["active"]:
            await bot.send(event, f"第{tid}队还没开，先让管理员发「丹丹组队{tid}」～"); return
        if uid in t["members"]:
            await bot.send(event, f"你已经在本队啦，当前 {len(t['members'])} 人"); return
        t["members"].append(uid); save_data(data)
        if len(t["members"]) >= MAX_MEMBER:
            ats = "".join(str(MessageSegment.mention_qid(q)) for q in t["members"])
            archive_team(tid)
            await bot.send(event, f"加入成功！当前人数{len(t['members'])}人\n已满员！\n{ats}")
        else:
            await bot.send(event, f"加入成功！当前人数{len(t['members'])}人")
        return

    if text.startswith("组队退出"):
        tid = 1 if "1" in text else 2
        t = get_team(tid)
        if not t or not t["active"]:
            await bot.send(event, f"第{tid}队没开着呢～"); return
        if uid in t["members"]:
            t["members"].remove(uid); save_data(data)
            await bot.send(event, f"退出成功！第{tid}队当前人数{len(t['members'])}人")
        else:
            await bot.send(event, "你不在本队里哦～")
        return

    if text.startswith("组队开始"):
        if not is_admin(event):
            await bot.send(event, "只有管理员才能存档哦～"); return
        tid = 1 if "1" in text else 2
        archive_team(tid)
        await bot.send(event, "组队已开始，已保存记录"); return

    if text.startswith("组队结束"):
        if not is_admin(event):
            await bot.send(event, "只有管理员才能结束组队～"); return
        tid = 1 if "1" in text else 2
        t = get_team(tid)
        if not t:
            await bot.send(event, f"第{tid}队本来就没开～"); return
        t["active"] = False; save_data(data)
        await bot.send(event, f"第{tid}队已停止组队"); return

    if text.startswith("组队备注"):
        if not is_admin(event):
            await bot.send(event, "只有管理员才能改备注～"); return
        tid = 1 if "1" in text else 2
        name = text.replace("组队备注1","").replace("组队备注2","").replace("组队备注","").strip()
        t = get_team(tid)
        if not t:
            await bot.send(event, f"第{tid}队还没开～"); return
        t["remark"] = name; t["name"] = name; save_data(data)
        await bot.send(event, f"组队{tid}备注成功，第{tid}队名称改为「{name}」"); return

    if text.startswith("组队计数"):
        tid = 1 if "1" in text else 2
        t = get_team(tid)
        if not t or not t["active"]:
            await bot.send(event, f"第{tid}队没开着呢～"); return
        lab = label(t) or f"第{tid}队"
        if not t["members"]:
            await bot.send(event, f"{lab} 已有 0 人"); return
        lines = [f"{lab} 已有 {len(t['members'])} 人："] + [f"{i}. {q}" for i, q in enumerate(t["members"], 1)]
        await bot.send(event, "\n".join(lines)); return

    if text.startswith("组队艾特"):
        tid = 1 if "1" in text else 2
        t = get_team(tid)
        if not t or not t["active"]:
            await bot.send(event, f"第{tid}队没开着呢～"); return
        lab = label(t) or f"第{tid}队"
        if not t["members"]:
            await bot.send(event, f"{lab} 暂时没人～"); return
        ats = "".join(str(MessageSegment.mention_qid(q)) for q in t["members"])
        diff = MAX_MEMBER - len(t["members"])
        if diff > 0:
            await bot.send(event, f"{lab}名单：\n{ats}\n(艾特完成 还差{diff}人满人)")
        else:
            await bot.send(event, f"{lab}名单：\n{ats}")
        return

    if text == "组队历史":
        hist = data.get("history", [])
        if not hist:
            await bot.send(event, "📜 还没有任何组队记录哦～"); return
        lines = ["📜 最近组队记录（含备注名）："] + [
            f"· {h.get('remark') or h.get('name') or ('第'+str(h.get('team_id'))+'队')}（{len(h.get('members',[]))}人）"
            for h in hist[-10:]
        ]
        await bot.send(event, "\n".join(lines)); return
