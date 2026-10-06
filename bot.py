import nonebot
from nonebot import init
from nonebot.adapters.qq import Adapter as QQAdapter
import logging

logging.basicConfig(level=logging.DEBUG)

nonebot.init(driver="~httpx+~websockets")

driver = nonebot.get_driver()
driver.register_adapter(QQAdapter)

nonebot.load_plugins("plugins")

nonebot.run()
