from nonebot import on_message
from nonebot.adapters.qq import Bot, Event

@on_message(priority=1).handle()
async def handle(bot: Bot, event: Event):
    uid = str(event.get_user_id())
    await bot.send(event, f"DEBUG你的ID是：{uid}")
    return
