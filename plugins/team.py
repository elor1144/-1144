from nonebot import on_message
from nonebot.adapters.qq import Bot, MessageSegment, Event
import json, os, asyncio, re

BASE = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE, "team_data.json")
MAX_MEMBER = 8
ADMIN_OPENIDS = {
    "8F33BB8A446515723B3EBACA4D5E6574",
    "BE17FB9434A14FFED902CDAE49C7B606",
    "FCE26E909EB5E50823B381543FD28CB0",
}

CMD_KEYWORDS = [
    "丹丹菜单", "丹丹组队", "定时提醒", "组队退出", "组队结束",
    "组队备注", "组队计数", "组队艾特", "组队历史",
]
GREET_WORDS = ["你好", "您好", "hi", "hello", "嗨", "在吗", "在么", "早", "早上好", "晚上好", "下午好"]

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
    uid = str(event.get_user_id())
    if uid in ADMIN_OPENIDS:
        return True
    for attr in ("member", "author"):
        role = getattr(getattr(event, attr, None), "role", None)
        if role in ("owner", "admin"):
            return True
    return False

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

@on_message(priority=1).handle()
async def handle(bot: Bot, event: Event):
    # ===== DEBUG 开始 =====
    try:
        print("[DEBUG] segments:", [(seg.type, seg.data) for seg in event.get_message()])
        print("[DEBUG] text:", repr(get_text(event)))
        print("[DEBUG] uid:", str(event.get_user_id()))
    except Exception as e:
        print("[DEBUG] err:", e)
    # ===== DEBUG 结束 =====

    text = get_text(event)
    if not text:
        await send_msgs(bot, event, "⭐这是什么意思呀？")
        return
    uid = str(event.get_user_id())

    if any(g in text.lower() for g in GREET_WORDS):
        await send_msgs(bot, event, "你好呀⭐")
        return

    if not any(kw in text for kw in CMD_KEYWORDS) and not re.search(r"\b[12]\b", text):
        await send_msgs(bot, event, "⭐这是什么意思呀？")
        return

    if "丹丹菜单" in text:
        await send_msgs(bot, event,
            "⭐ 组队助手 菜单\n━━━━━━━━\n"
            "💫【开队】丹丹组队1 / 丹丹组队2（管理员，开队即存档）\n"
            "💫【加入】发 1 玩家名 角色 加入队伍\n"
            "💫【退出】组队退出1 / 组队退出2（自己退）\n"
            "💫【帮退】组队退出1 @某人 / 组队退出2 @某人（管理员）\n"
            "💫【结束】组队结束1 / 组队结束2（管理员）\n"
            "💫【备注】组队备注1 / 组队备注2 + 名称（管理员）\n"
            "💫【定时】定时提醒 10分钟 内容（管理员）\n"
            "💫【计数】组队计数1 / 组队计数2\n"
            "💫【艾特】组队艾特1 / 组队艾特2\n"
            "💫【历史】组队历史\n━━━━━━━━\n满8人自动艾特")
        return

    if "丹丹组队" in text:
        if not is_admin(event):
            await send_msgs(bot, event, "[error] 只有管理员才能开队哦～"); return
        tid = 1 if "1" in text else 2
        t = get_team(tid)
        if t and t["active"]:
            await send_msgs(bot, event, f"[error] 第{tid}队已经在开了～"); return
        new_team(tid)
        archive_team(tid)
        await send_msgs(bot, event, f"第{tid}队已开启，最多两队并存～\n想加入的直接发「1 你的玩家名 你的角色」即可")
        return

    if "定时提醒" in text:
        if not is_admin(event):
            await send_msgs(bot, event, "[error] 只有管理员才能设提醒哦～"); return
        body = text.split("定时提醒", 1)[1].strip()
        mm = re.match(r"^(\d+\s*(?:分钟|分|小时|时|秒))\s*(.*)$", body)
        if not mm:
            await send_msgs(bot, event, "[error] 格式：定时提醒 10分钟 提醒内容"); return
        secs = parse_duration(mm.group(1))
        msg = mm.group(2).strip() or "时间到，组队提醒！"
        if secs is None:
            await send_msgs(bot, event, "[error] 时间格式不对，用 分钟/小时/秒"); return
        await send_msgs(bot, event, f"已设置 {mm.group(1)} 后提醒")
        await asyncio.sleep(secs)
        await send_msgs(bot, event, f"⏰ 提醒：{msg}")
        return

    m = re.search(r"\b([12])\s+(\S+)\s+(\S+)$", text)
    if m:
        tid = int(m.group(1)); nick = m.group(2); role = m.group(3)
        t = get_team(tid)
        if not t or not t["active"]:
            await send_msgs(bot, event, f"[error] 第{tid}队还没开，先发「丹丹组队{tid}」～"); return
        if uid in t["members"]:
            await send_msgs(bot, event, f"[error] 你已经在本队啦，当前 {len(t['members'])} 人"); return
        t["members"][uid] = {"openid": uid, "nick": nick, "role": role}
        save_data(data)
        cnt = len(t["members"])
        shown = f"{nick}（角色：{role}）"
        if cnt >= MAX_MEMBER:
            ats = "".join(at_seg(v["openid"], v.get("nick","")) for v in t["members"].values())
            archive_team(tid)
            await send_msgs(bot, event, f'第{tid}队："{(label(t) or "第"+str(tid)+"队")}"\n已满员！\n{ats}')
        else:
            await send_msgs(bot, event, f"加入成功！当前人数{cnt}人\n名称：{shown}")
        return

    if re.search(r"\b[12]\b", text):
        await send_msgs(bot, event, "[error] 格式不对～ 请按：1 你的玩家名 你的角色（例：1 呃呃 彩球）"); return

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
            await send_msgs(bot, event, f"已帮 {len(removed)} 人从第{tid}队退出，当前 {len(t['members'])} 人")
        else:
            await send_msgs(bot, event, f"[error] 被@的人不在第{tid}队里哦～")
        return

    if "组队退出" in text:
        tid = 1 if "1" in text else 2
        t = get_team(tid)
        if not t or not t["active"]:
            await send_msgs(bot, event, f"[error] 第{tid}队没开着呢～"); return
        if uid in t["members"]:
            t["members"].pop(uid, None); save_data(data)
            await send_msgs(bot, event, f"退出成功！第{tid}队当前人数{len(t['members'])}人")
        else:
            await send_msgs(bot, event, "[error] 你不在本队里哦～")
        return

    if "组队结束" in text:
        if not is_admin(event):
            await send_msgs(bot, event, "[error] 只有管理员才能结束组队～"); return
        tid = 1 if "1" in text else 2
        t = get_team(tid)
        if not t:
            await send_msgs(bot, event, f"[error] 第{tid}队本来就没开～"); return
        t["active"] = False; save_data(data)
        await send_msgs(bot, event, f"第{tid}队已停止组队"); return

    if "组队备注" in text:
        if not is_admin(event):
            await send_msgs(bot, event, "[error] 只有管理员才能改备注～"); return
        tid = 1 if "1" in text else 2
        name = text.split("组队备注", 1)[1]
        name = name[1:].strip() if name and name[0] in "12" else name.strip()
        t = get_team(tid)
        if not t:
            await send_msgs(bot, event, f"[error] 第{tid}队还没开～"); return
        t["remark"] = name; t["name"] = name; save_data(data)
        await send_msgs(bot, event, f"组队{tid}备注成功，第{tid}队名称改为「{name}」"); return

    if "组队计数" in text:
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

    if "组队艾特" in text:
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

    if "组队历史" in text:
        hist = data.get("history", [])
        if not hist:
            await send_msgs(bot, event, "📜 还没有任何组队记录哦～"); return
        lines = ["📜 最近组队记录（含备注名）："] + [
            f"· {h.get('remark') or h.get('name') or ('第'+str(h.get('team_id'))+'队')}（{len(h.get('members',[]))}人）"
            for h in hist[-10:]
        ]
        await send_msgs(bot, event, "\n".join(lines)); return
