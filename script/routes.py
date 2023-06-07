import json
import time
import uuid

from fastapi import Body, HTTPException
from starlette.background import BackgroundTasks
from lib.lang import lang
from controller.watch import create_service


def route_registration(fastApp, fastDb):
    @fastApp.get("/")
    async def root():
        return {"code": 200, "message": "欢迎使用AutoSync"}

    @fastApp.post("/api/run_watch_service")
    async def run_watch_service(
            background_tasks: BackgroundTasks,
            body=Body(),
    ):
        config = fastDb.find("watch_service", "*", "UUID=?", (body['UUID'],))
        if config is None:
            # UUID不正确
            raise HTTPException(status_code=400, detail=lang("UUID ERROR"))
        print(config)
        create_service(background_tasks, fastDb, config)
        pass

    @fastApp.post("/api/create_watch_service")
    async def create_watch_service(
            NAME=Body(""),
            DEV_TYPE=Body("local_to_ftp"),
            SYNC_TYPE=Body("30"),
            TIMEER_CONFIG=Body({}),
            DEV_CONFIG=Body({}),
            SYNC_DIR=Body({}),
            SORT_BY=Body(100),
            RECYCLE_OPEN=Body('0'),
            RECYCLE_CONFIG=Body({}),
    ):
        if DEV_TYPE not in ['local_to_ftp']:
            # 服务驱动类型不支持
            raise HTTPException(status_code=400, detail=lang("ServiceDevSupport"))
        NAME = str(NAME).strip()
        if NAME == "":
            # 服务名称不能为空
            raise HTTPException(status_code=400, detail=lang("ServiceNameEmpty"))

        if fastDb.existData("watch_service", {
            'NAME': NAME
        }):
            # 服务名称已存在
            raise HTTPException(status_code=400, detail=lang("ServiceExists"))
        [UUID, _] = fastDb.save_watch_service(NAME, DEV_TYPE, DEV_CONFIG, SYNC_TYPE, TIMEER_CONFIG, SYNC_DIR,
                                              int(SORT_BY),
                                              int(RECYCLE_OPEN), RECYCLE_CONFIG)

        return {"code": 200, "message": lang('ServiceCreateSuccess'), "uuid": UUID}
