import json
import os

import script.app as app
from lib.wprint import pretty
from service.sync import create_transmit_device


def get_watch_config():
    watch_config: dict | None = None
    if os.path.exists("./watch.json"):
        with open("./watch.json", "r") as f:
            watch_config = json.loads(f.read().encode(encoding='gbk'))
    return watch_config


if __name__ == '__main__':
    # pretty("+", 123123)
    # pretty("-", 123123)
    # pretty("*", 123123)
    # pretty("!", 123123)
    # 创建服务
    app.run("./config.ini", get_watch_config())
    # # 本地驱动测试
    # dc = create_transmit_device({
    #     "device": "LOCAL",
    #     "root": "D:\\Test1\\ABCDEFG",
    # })
    # print(dc.sync_all())
    # # FTP驱动测试
    # dv = create_transmit_device({
    #     "device": "FTP",
    #     "host": "",
    #     "port": 21,
    #     "username": "",
    #     "password": "",
    #     "root": "/"
    # })
    # print(dv.mkdir(r"/CCC//xgFGA"))
    # print(dv.unlink(r"/CCC/xgFGA"))
    # print(dv.rename(r'/CCC/xgCC', '/CCCxgCC3'))
    # print(dv.rename(r'/xx.txt', '/xt.txt'))
    # print(dv.lists("/ABCDEFG"))
