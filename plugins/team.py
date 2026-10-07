import traceback
from nonebot import on_message
from nonebot.adapters.qq import Bot, Event

@on_message(priority=1).handle()
async def handle(bot: Bot, event: Event):
    try:
        msg = str(event.get_message())
        await bot.send(event, "探针收到消息：" + msg[:30])
    except Exception as e:
        print("[PROBE-ERROR]", traceback.format_exc())
