import nonebot
from nonebot import init
from nonebot.adapters.qq import Adapter as QQAdapter
import logging
import os
import json

logging.basicConfig(level=logging.DEBUG)

# 打印实际读到的配置，确认 Railway 变量有没有正确传进来
raw = os.environ.get("QQ_BOTS", "")
print("=== QQ_BOTS RAW ===")
print(raw)
try:
    cfg = json.loads(raw)
    s = cfg[0].get("secret", "")
    print("=== secret 长度:", len(s), "首尾:", s[:4], s[-4:], "===")
except Exception as e:
    print("解析失败:", e)

nonebot.init(driver="~httpx+~websockets")

driver = nonebot.get_driver()
driver.register_adapter(QQAdapter)

nonebot.load_plugins("plugins")

nonebot.run()
