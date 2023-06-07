import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import lib.db as db
from service.config import ConfigService
from script.routes import route_registration

fastDb = db.LiteDb()
fastDb.openDb(os.path.abspath("./database.db"))
if fastDb.existTable('watch_service') is False:
    # 同步服务
    watch_service_fields = [
        "ID integer PRIMARY KEY AUTOINCREMENT",
        "UUID varchar(36) not null",  # 创建一个唯一的UUID
        "NAME varchar(100) not null",  # 服务名称
        "DEV_TYPE varchar(20) default 'local_to_ftp'",  # 驱动类型 ( 默认并且暂时只支持 本地文件同步到FTP
        "DEV_CONFIG text not null",  # 驱动配置
        "SYNC_TYPE int default 10",  # 同步方式 ( 10实时同步, 20定时同步)
        "TIMEER_CONFIG varchar(100) default ''",  # 定时同步配置
        "SYNC_DIR text not null",  # 同步目录映射关系
        "ADD_TIME int not null",  # 服务创建时间
        "STATUS varchar(2) default '0'",  # 服务状态  ( 0未开启， 1已开启)
        "SORT_BY int default 100",  # 排序号
        "RECYCLE_OPEN int default 0",  # 是否启用回收站功能 - 会产生大量日志记录和备份数据
        "RECYCLE_CONFIG text not null",  # 回收站配置
    ]
    fastDb.createTable("create table watch_service(" + (",".join(watch_service_fields)) + ")")
    print("[DB日志]", "创建了表`watch_service`")
if fastDb.existTable('file_recycle') is False:
    # 回收站 - 对文件修改/删除有效
    file_recycle_fields = [
        "ID integer PRIMARY KEY AUTOINCREMENT",
        "NAME varchar(512) not null",  # 文件名称(最大支持512位
        "MD5 varchar(20) not null",  # 文件MD5
        "TIME int not null",  # 操作时间
        "SID int not null",  # 服务ID
    ]
    fastDb.createTable("create table file_recycle(" + (",".join(file_recycle_fields)) + ")")
    print("[DB日志]", "创建了表`file_recycle`")


class FastApp(FastAPI):
    config: ConfigService

    def __init__(self, config: ConfigService):
        self.config = config
        super().__init__(title="AutoSyncTool",
                         debug=config.getBoolean('APP.DEBUG', False),
                         description="""
            文件自动同步工具. 🚀
            """,
                         version="1.0.1",
                         contact={
                             "name": "狡猾的骗骗花",
                             "url": "http://nya.kim",
                             "email": "u2nyakim@gmail.com",
                         })

    def run(self):
        uvicorn.run(
            app=self,
            host=self.config.get('APP.LISTEN_HOST', '0.0.0.0'),
            port=self.config.getInt('APP.LISTEN_PORT', 52077),
            reload=False
        )


fastApp: FastApp


def run(config_file: str, watch_config: dict = None):
    if watch_config is not None and 'services' in watch_config:
        for d in watch_config['services']:
            fastDb.delete_watch_service({
                'NAME': d['NAME']
            })
            if 'SYNC_TYPE' not in d:
                d['SYNC_TYPE'] = "30"
            if 'SORT_BY' not in d:
                d['SORT_BY'] = 100
            if 'RECYCLE_OPEN' not in d:
                d['RECYCLE_OPEN'] = 0
            if 'RECYCLE_CONFIG' not in d:
                d['RECYCLE_CONFIG'] = {}
            [UUID, _] = fastDb.save_watch_service(d['NAME'], d['DEV_TYPE'], d['DEV_CONFIG'], d['SYNC_TYPE'],
                                                  d['TIMEER_CONFIG'], d['SYNC_DIR'],
                                                  int(d['SORT_BY']),
                                                  int(d['RECYCLE_OPEN']), d['RECYCLE_CONFIG'])
            print("SERVICE " + d['NAME'] + " UUID", UUID)
    global fastApp
    """载入配置文件"""
    config_file = os.path.abspath(config_file)
    print("load config file", config_file)
    """创建应用"""
    fastApp = FastApp(ConfigService(config_file))
    """应用中间件"""
    fastApp.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "*",
            "http://localhost",
            "http://localhost:5173"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    fastApp.mount("/web", StaticFiles(directory="web"), name="web")
    """注册路由接口"""
    route_registration(fastApp, fastDb)
    """运行Http服务
           :return:
           """
    fastApp.run()
