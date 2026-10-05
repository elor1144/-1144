import os
import nonebot
from nonebot import init
from nonebot.adapters.qq import Adapter as QQAdapter

nonebot.init(
    qq_botid=os.environ.get("QQ_BOTID"),
    qq_client_secret=os.environ.get("QQ_CLIENT_SECRET"),
)

driver = nonebot.get_driver()
driver.register_adapter(QQAdapter)

nonebot.load_plugins("plugins")

nonebot.run()
