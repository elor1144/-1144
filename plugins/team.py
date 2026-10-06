from nonebot import on_command
from nonebot.adapters.qq import MessageEvent
import re

team_data = {}

team = on_command("组队", priority=5)
count = on_command("计数", priority=5)
remark = on_command("备注", priority=5)

@count.handle()
async def _(event: MessageEvent):
    gid = event.get_group_id()
    data = team_data.get(gid, {"members": []})
    await count.finish(f"当前已组队 {len(data['members'])} 人")

@remark.handle()
async def _(event: MessageEvent):
    gid = event.get_group_id()
    text = event.get_plaintext().strip()
    m = re.search(r"备注\s*(\S+)\s*(.+)", text)
    if not m:
        await remark.finish("用法：组队备注1 丹丹跑")
    name, note = m.group(1), m.group(2)
    if gid not in team_data:
        team_data[gid] = {"members": [], "remark": {}}
    team_data[gid]["remark"][name] = note
    await remark.finish(f"已记录 {name} 的备注：{note}")
