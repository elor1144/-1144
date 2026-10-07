from nonebot import on_message
from nonebot.adapters.qq import Bot, Event

@on_message(priority=1).handle()
async def handle(bot: Bot, event: Event):
    try:
        await bot.send(event, "我活着")
    except Exception as e:
        print("[ERR]", e)
