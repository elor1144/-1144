import nonebot
from nonebot.adapters.qq import Adapter as QQAdapter

nonebot.init()
nonebot.register_adapter(QQAdapter)
nonebot.load_plugins("plugins")
nonebot.run()
