from nonebot import on_message
from nonebot.adapters.qq import Bot, MessageSegment, Event
import json, os, asyncio, re, difflib

BASE = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE, "team_data.json")
MAX_MEMBER = 8
ADMIN_OPENIDS = {
    "8F33BB8A446515723B3EBACA4D5E6574",
    "BE17FB9434A14FFED902CDAE49C7B606",
    "FCE26E909EB5E50823B381543FD28CB0",
}
ALLOWED_GROUPS = {
    "E96253B3683DD2B9E4270027306D107D",
    "02974B8091D2AF0865C73C36E4D22B5E",
}

GREET_WORDS = ["你好", "您好", "hi", "hello", "嗨", "在吗", "在么", "早", "早上好", "晚上好", "下午好"]

CORE_CMDS = ["丹丹菜单", "丹丹组队", "组队退出", "组队结束", "组队结束all",
             "组队备注", "组队计数", "组队艾特", "组队历史", "定时提醒", "星星保修", "删除历史all"]

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

async def send_msgs(bot, event, text):
    try:
        await bot.send(event, text)
    except Exception:
        try:
            await event.reply(text)
        except Exception:
            try:
                await bot.send(event, MessageSegment.text(text))
            except Exception:
                pass

def is_admin(event):
    gid = str(getattr(event, "group_id", "") or getattr(event, "guild_id", ""))
    if ALLOWED_GROUPS and gid and gid not in ALLOWED_GROUPS:
        return False
    return str(event.get_user_id()) in ADMIN_OPENIDS

def get_mentions(event):
    res = []
    for seg in event.get_message():
        if seg.type == "mention":
            uid = str(seg.data.get("user_id", ""))
            if uid:
                res.append(uid)
    return res

def get_text(event):
    out = ""
    for seg in event.get_message():
        t = seg.type
        if t in ("text", "plain"):
            out += seg.data.get("text", "")
        elif t == "mention":
            out += " @"
    return out.strip().strip("！!。.，,~～ ").strip()

def get_team(tid):
    return data["teams"].get(str(tid))

def team_open(tid):
    t = get_team(tid)
    return bool(t and t.get("active"))

def new_team(tid):
    data["teams"][str(tid)] = {"members": {}, "remark": "", "active": True, "name": ""}
    save_data(data)

def archive_team(tid):
    t = get_team(tid)
    if not t:
        return
    data.setdefault("history", [])
    snap = {"team_id": tid, "remark": t.get("remark",""), "name": t.get("name",""),
            "members": [ {"openid": k, **v} for k, v in t["members"].items() ]}
    data["history"].append(snap)
    if len(data["history"]) > 50:
        data["history"] = data["history"][-50:]
    save_data(data)

def label(t):
    return t.get("remark") or t.get("name") or ""

def parse_duration(s):
    m = re.match(r"^(\d+)\s*(分钟|分|小时|时|秒)$", s)
    if not m:
        return None
    n = int(m.group(1)); unit = m.group(2)
    if unit in ("分钟", "分"):
        return n * 60
    if unit in ("小时", "时"):
        return n * 3600
    if unit == "秒":
        return n
    return None

def at_seg(openid, nick=""):
    try:
        return str(MessageSegment.mention_user(user_id=openid))
    except Exception:
        try:
            return str(MessageSegment.mention_qid(openid))
        except Exception:
            return f"@{nick}" if nick else str(openid)

def is_exact(text, keyword):
    return re.fullmatch(rf"{re.escape(keyword)}\s*[12]?\s*[！!。．.，,~～ ]*", text) is not None

def only_keyword_no_num(text, keyword):
    return re.fullmatch(rf"{re.escape(keyword)}\s*[！!。．.，,~～ ]*", text) is not None

def guess_cmd(text):
    s = text.strip().strip("！!。．.，,~～ ")
    num = ""
    m = re.fullmatch(r"(.*?)\s*([12])\s*$", s)
    if m:
        s, num = m.group(1).strip(), m.group(2)
    if re.search(r"a\s*l\s*l?", s) or "all" in s.lower():
        base = re.sub(r"a\s*l+\s*$", "", s, flags=re.I).strip()
        if difflib.SequenceMatcher(None, base, "组队结束").ratio() > 0.5 or base == "":
            return "组队结束all"
    match = difflib.get_close_matches(s, CORE_CMDS, n=1, cutoff=0.55)
    if not match:
        return None
    best = match[0]
    if best == "组队结束all":
        return "组队结束all"
    if best in ("组队备注", "定时提醒", "星星保修", "删除历史all"):
        return best
    return best + num

@on_message(priority=1).handle()
async def handle(bot: Bot, event: Event):
    text = get_text(event)
    if not text:
        return
    uid = str(event.get_user_id())

    if is_exact(text, "调试群ID"):
        await send_msgs(bot, event, "群ID=" + str(getattr(event, "group_id", "") or getattr(event, "guild_id", "") or "无"))
        return

    if any(g in text.lower() for g in GREET_WORDS):
        await send_msgs(bot, event, "你好呀⭐")
        return

    if is_exact(text, "丹丹菜单"):
        await send_msgs(bot, event,
            "⭐ 组队助手 菜单\n━━━━━━━━\n"
            "💫【开队】丹丹组队1 / 丹丹组队2（管理员，开队即存档）\n"
            "💫【加入】发 1 玩家名 角色 加入队伍\n"
            "💫【退出】组队退出1 / 组队退出2（自己退）\n"
            "💫【帮退】组队退出1 @某人 / 组队退出2 @某人（管理员）\n"
            "💫【结束】组队结束1 / 组队结束2（管理员）\n"
            "💫【结束all】组队结束all（需1、2队都开启，管理员）\n"
            "💫【备注】组队备注1 / 组队备注2 + 名称（管理员）\n"
            "💫【定时】定时提醒 10分钟 内容（管理员）\n"
            "💫【计数】组队计数1 / 组队计数2\n"
            "💫【艾特】组队艾特1 / 组队艾特2\n"
            "💫【保修】星星保修（修复已知问题）\n"
            "💫【删历史】删除历史all（清空记录，管理员）\n"
            "💫【历史】组队历史\n━━━━━━━━\n满8人自动艾特")
        return

    if only_keyword_no_num(text, "丹丹组队"):
        await send_msgs(bot, event, "[error]请加上队伍号！(在后面加上1/2)"); return

    if is_exact(text, "丹丹组队"):
        if not is_admin(event):
            await send_msgs(bot, event, "[error] 只有管理员才能开队哦～"); return
        tid = 1 if "1" in text else 2
        t = get_team(tid)
        if t and t["active"]:
            await send_msgs(bot, event, f"[error] 第{tid}队已经在开了～"); return
        if tid == 2 and not team_open(1):
            await send_msgs(bot, event, "[error]请先开启第1队！"); return
        new_team(tid)
        archive_team(tid)
        await send_msgs(bot, event, f"⭐ 第{tid}队已开启，最多两队并存～\n想加入的直接发「1 你的玩家名 你的角色」即可")
        return

    if text.startswith("定时提醒"):
        body = text[len("定时提醒"):].strip()
        mm = re.match(r"^(\d+\s*(?:分钟|分|小时|时|秒))\s*(.*)$", body)
        if not mm:
            await send_msgs(bot, event, "[error] 格式：定时提醒 10分钟 提醒内容"); return
        if not is_admin(event):
            await send_msgs(bot, event, "[error] 只有管理员才能设提醒哦～"); return
        secs = parse_duration(mm.group(1))
        msg = mm.group(2).strip() or "时间到，组队提醒！"
        if secs is None:
            await send_msgs(bot, event, "[error] 时间格式不对，用 分钟/小时/秒"); return
        await send_msgs(bot, event, f"⭐ 已设置 {mm.group(1)} 后提醒")
        await asyncio.sleep(secs)
        await send_msgs(bot, event, f"⏰ 提醒：{msg}")
        return

    m = re.search(r"\b([12])\s+(\S+)\s+(\S+)$", text)
    if m:
        tid = int(m.group(1))
        if not team_open(tid):
            return
        nick = m.group(2); role = m.group(3)
        t = get_team(tid)
        if uid in t["members"]:
            await send_msgs(bot, event, f"[error] 你已经在本队啦，当前 {len(t['members'])} 人"); return
        t["members"][uid] = {"openid": uid, "nick": nick, "role": role}
        save_data(data)
        cnt = len(t["members"])
        shown = f"{nick}（角色：{role}）"
        if cnt >= MAX_MEMBER:
            ats = "".join(at_seg(v["openid"], v.get("nick","")) for v in t["members"].values())
            archive_team(tid)
            await send_msgs(bot, event, f'⭐ 第{tid}队："{(label(t) or "第"+str(tid)+"队")}"\n已满员！\n{ats}')
        else:
            await send_msgs(bot, event, f"⭐ 加入成功！当前人数{cnt}人\n名称：{shown}")
        return

    if re.fullmatch(r"[12]\s*[！!。．.，,~～ ]*", text):
        tid = int(text.strip()[0])
        if not team_open(tid):
            return
        await send_msgs(bot, event, "[error] 格式不对～ 请按：1 你的玩家名 你的角色（例：1 呃呃 彩球）"); return

    if only_keyword_no_num(text, "组队退出"):
        await send_msgs(bot, event, "[error]请加上队伍号！(在后面加上1/2)"); return

    if "组队退出" in text and get_mentions(event):
        if not is_admin(event):
            await send_msgs(bot, event, "[error] 只有管理员才能帮别人退队哦～"); return
        tid = 1 if "1" in text else 2
        targets = get_mentions(event)
        t = get_team(tid)
        if not t or not t["active"]:
            await send_msgs(bot, event, f"[error] 第{tid}队没开着呢～"); return
        removed = [tg for tg in targets if tg in t["members"]]
        for tg in removed:
            t["members"].pop(tg, None)
        save_data(data)
        if removed:
            await send_msgs(bot, event, f"⭐ 已帮 {len(removed)} 人从第{tid}队退出，当前 {len(t['members'])} 人")
        else:
            await send_msgs(bot, event, f"[error] 被@的人不在第{tid}队里哦～")
        return

    if is_exact(text, "组队退出"):
        tid = 1 if "1" in text else 2
        t = get_team(tid)
        if not t or not t["active"]:
            await send_msgs(bot, event, f"[error] 第{tid}队没开着呢～"); return
        if uid in t["members"]:
            t["members"].pop(uid, None); save_data(data)
            await send_msgs(bot, event, f"⭐ 退出成功！第{tid}队当前人数{len(t['members'])}人")
        else:
            await send_msgs(bot, event, "[error] 你不在本队里哦～")
        return

    if only_keyword_no_num(text, "组队结束"):
        await send_msgs(bot, event, "[error]请加上队伍号！(在后面加上1/2)"); return

    if is_exact(text, "组队结束"):
        if not is_admin(event):
            await send_msgs(bot, event, "[error] 只有管理员才能结束组队～"); return
        tid = 1 if "1" in text else 2
        t = get_team(tid)
        if not t:
            await send_msgs(bot, event, f"[error] 第{tid}队本来就没开～"); return
        t["active"] = False; save_data(data)
        await send_msgs(bot, event, f"⭐ 第{tid}队已停止组队")
        return

    if is_exact(text, "组队结束all"):
        if not is_admin(event):
            await send_msgs(bot, event, "[error] 只有管理员才能结束组队～"); return
        if not (team_open(1) and team_open(2)):
            await send_msgs(bot, event, "[error]无法使用all指令！"); return
        for tid in (1, 2):
            t = get_team(tid)
            archive_team(tid)
            t["active"] = False; save_data(data)
        await send_msgs(bot, event, "⭐ 已结束第1、2队")
        return

    if is_exact(text, "星星保修"):
        for tid in list(data["teams"].keys()):
            if not data["teams"][tid].get("active") and not data["teams"][tid].get("members"):
                data["teams"].pop(tid, None)
        save_data(data)
        await send_msgs(bot, event, "⭐ 已修复已知问题，感谢反馈！如仍有异常请稍后重试～")
        return

    if is_exact(text, "删除历史all"):
        if not is_admin(event):
            await send_msgs(bot, event, "[error] 只有管理员才能删除历史记录哦～"); return
        data["history"] = []
        save_data(data)
        await send_msgs(bot, event, "⭐ 已清空所有组队历史记录")
        return

    if only_keyword_no_num(text, "组队备注"):
        await send_msgs(bot, event, "[error]请加上队伍号！(在后面加上1/2)"); return

    if text.startswith("组队备注"):
        if not is_admin(event):
            await send_msgs(bot, event, "[error] 只有管理员才能改备注～"); return
        tid = 1 if "1" in text else 2
        name = text[len("组队备注"):].strip()
        name = name[1:].strip() if name and name[0] in "12" else name
        t = get_team(tid)
        if not t:
            await send_msgs(bot, event, f"[error] 第{tid}队还没开～"); return
        if not name:
            await send_msgs(bot, event, "[error] 格式：组队备注1 队伍名称"); return
        t["remark"] = name; t["name"] = name; save_data(data)
        await send_msgs(bot, event, f"⭐ 组队{tid}备注成功，第{tid}队名称改为「{name}」"); return

    if only_keyword_no_num(text, "组队计数"):
        await send_msgs(bot, event, "[error]请加上队伍号！(在后面加上1/2)"); return

    if is_exact(text, "组队计数"):
        tid = 1 if "1" in text else 2
        t = get_team(tid)
        if not t or not t["active"]:
            await send_msgs(bot, event, f"[error] 第{tid}队没开着呢～"); return
        lab = label(t) or f"第{tid}队"
        if not t["members"]:
            await send_msgs(bot, event, f'第{tid}队："{lab}"\n当前成员：\n（暂无）'); return
        lines = [f'第{tid}队："{lab}"', "当前成员："]
        for i, v in enumerate(t["members"].values(), 1):
            nm = v.get("nick") or ""
            rl = v.get("role") or ""
            lines.append(f"{i}. {nm}（角色：{rl}）")
        await send_msgs(bot, event, "\n".join(lines)); return

    if only_keyword_no_num(text, "组队艾特"):
        await send_msgs(bot, event, "[error]请加上队伍号！(在后面加上1/2)"); return

    if is_exact(text, "组队艾特"):
        tid = 1 if "1" in text else 2
        t = get_team(tid)
        if not t or not t["active"]:
            await send_msgs(bot, event, f"[error] 第{tid}队没开着呢～"); return
        lab = label(t) or f"第{tid}队"
        if not t["members"]:
            await send_msgs(bot, event, f"[error] {lab} 暂时没人～"); return
        lines = [f"{lab}名单（已加入 {len(t['members'])} 人）："]
        for v in t["members"].values():
            at = at_seg(v["openid"], v.get("nick",""))
            nm = v.get("nick") or ""
            rl = v.get("role") or ""
            lines.append(f"{at} {nm}（角色：{rl}）")
        diff = MAX_MEMBER - len(t["members"])
        msg = "\n".join(lines)
        if diff > 0:
            msg += f"\n(艾特完成 还差{diff}人满人)"
        await send_msgs(bot, event, msg)
        return

    if is_exact(text, "组队历史"):
        hist = data.get("history", [])
        if not hist:
            await send_msgs(bot, event, "📜 还没有任何组队记录哦～"); return
        lines = ["📜 最近组队记录（含备注名）："]
        for i, h in enumerate(hist[-10:], 1):
            tid = h.get("team_id")
            now_tag = " [now]" if team_open(tid) else ""
            name = h.get("remark") or h.get("name") or (f"第{tid}队")
            cnt = len(h.get("members", []))
            lines.append(f"{i}. {name}（{cnt}人）{now_tag}")
        await send_msgs(bot, event, "\n".join(lines)); return

    if text.startswith("组队"):
        await send_msgs(bot, event, "[error]请加上队伍号！(在后面加上1/2)"); return

    guessed = guess_cmd(text)
    if guessed:
        await send_msgs(bot, event, f"[提示]猜你想发！({guessed})"); return
