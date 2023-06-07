from service.sync import SyncService


def create_service(background_tasks, fastDb, config):
    # 创建同步服务
    ser = SyncService(fastDb, **config)
    ser.init()
    # 扔进后台进程执行
    background_tasks.add_task(ser.listen)
