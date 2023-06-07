import os

from watchdog.observers import Observer

from lib.wprint import pretty
from script.transmit import TransmitBase, LocalDrive as LocalTransmitDrive, FtpDrive as FtpTransmitDrive
from service.file_watch import FileEventHandler
from abc import ABC


class DevConfig:
    """驱动配置类"""

    def __init__(self, **entries):
        self.__dict__.update(entries)

    def get(self, name):
        return self.__dict__.get(name)

    pass


class BaseDevice(ABC):
    """设备传输驱动"""
    transporter: TransmitBase

    def __init__(self, transmitDevice):
        self.transporter = transmitDevice

    def read(self, filename):
        return self.transporter.read(filename)

    def upload(self, path, file):
        return self.transporter.upload(path, file)

    def path_relative(self, path: str):
        return path.replace(self.transporter.config.get('root'), "").replace("\\", "/")

    def mkdir(self, path):
        print("创建目录", path)
        return self.transporter.mkdir(path)

    def unlink(self, path):
        print("删除目录", path)
        return self.transporter.unlink(path)

    def rename(self, src_path, dst_path):
        print("重命名目录", src_path + " => " + dst_path)
        return self.transporter.rename(src_path, dst_path)

    def delete(self, src_path) -> bool:
        print("删除文件", src_path)
        return self.transporter.delete(src_path)

    def all_directory(self, src_path: str = "") -> list:
        return self.transporter.all_directory(src_path)


class SrcDevice(BaseDevice):
    """设备A"""
    pass


class DstDevice(BaseDevice):
    """设备B"""
    dir_map: dict = {}

    def bind_sync_dir(self, SYNC_DIR):
        self.dir_map = {}
        for d in SYNC_DIR:
            self.dir_map[d['src']] = d['dst']
        return self.dir_map


def default(data, name, default_value=None):
    if name not in data:
        return default_value
    return data[name]


def create_transmit_device(config: dict):
    if config['device'] == "LOCAL":
        return LocalTransmitDrive(
            root=default(config, 'root', '/')
        )
    if config['device'] == "FTP":
        return FtpTransmitDrive(
            host=default(config, 'host', '127.0.0.1'),
            port=int(default(config, 'port', 21)),
            username=default(config, 'username', ''),
            password=default(config, 'password', ''),
            root=default(config, 'root', '/')
        )


class SyncService:
    observer: Observer
    srcDevice: SrcDevice
    dstDevice: DstDevice

    DEV_CONFIG: DevConfig = {}
    SYNC_DIR: []
    DEV_TYPE: ""

    def __init__(self, db, **entries):
        self.db = db
        self.__dict__.update(entries)
        self.DEV_CONFIG = DevConfig(**entries['DEV_CONFIG'])

    def init(self):
        self.DEV_TYPE = (self.DEV_CONFIG.get('src')['device'] + '_to_' + self.DEV_CONFIG.get('dst')['device']).lower()
        print("[正在扫描要同步的目录]", "=============================")
        for d in self.SYNC_DIR:
            print("[目录]: ", d['src'] + " ====> " + d['dst'])
        print("一共有" + str(len(self.SYNC_DIR)) + "个可用映射目录")
        print("====================================================")
        print("开始载入设备A驱动")
        self.srcDevice = SrcDevice(transmitDevice=create_transmit_device(self.DEV_CONFIG.get('src')))
        print("==============")
        print("开始载入设备B驱动")
        self.dstDevice = DstDevice(transmitDevice=create_transmit_device(self.DEV_CONFIG.get('dst')))
        self.dstDevice.bind_sync_dir(self.SYNC_DIR)
        print("==============")
        self.observer = Observer()
        # 注册事件服务
        # ===========================================================
        event = FileEventHandler(self)
        for dir_ in self.SYNC_DIR:
            self.observer.schedule(event, dir_['src'], True)

    def listen(self):
        print("正在监听进程响应")
        self.observer.start()
        self.on("sync", data={
            "srcPath": self.srcDevice.transporter.config.get('root'),
            "dstPath": self.dstDevice.transporter.config.get("root")
        })
        self.observer.join()

    def filter_check(self, path, rule):
        is_sync = True
        if len(rule['contains']) > 0:
            # 1. 放行规则
            is_sync = False
            for file_type in rule['contains']:
                if path.endswith(file_type):
                    is_sync = True
        if len(rule['exclude']) > 0:
            # 2. 排除规则
            for file_type in rule['exclude']:
                if path.endswith(file_type):
                    is_sync = False
        return is_sync

    def get_dir(self, path):
        root_info: dict = {}
        for d in self.SYNC_DIR:
            if str(path).startswith(d['src']):
                root_info = d
        return root_info

    def on(self, name: str, data: dict):
        print("Event:on_" + name, data)

        if name == "sync":
            dirs = self.srcDevice.all_directory()
            for sub_folder in dirs[0:]:
                self.dstDevice.mkdir(path=self.srcDevice.path_relative(sub_folder))
                sub_list = os.listdir(sub_folder)
                file_map = dict({})
                for d in self.dstDevice.transporter.lists(self.srcDevice.path_relative(sub_folder)):
                    file_map[d['name']] = d
                for item in sub_list:
                    item_path = sub_folder + "\\" + item
                    file = self.srcDevice.transporter.info(item_path)
                    if file['type'] == 'file':
                        is_upload = True
                        src_relative_path = self.srcDevice.path_relative(file['path'])
                        global_filter = self.DEV_CONFIG.get('global_filter')
                        root_info = self.get_dir(file['path'])
                        root_info['filter']['contains'].extend(global_filter['contains'])
                        root_info['filter']['exclude'].extend(global_filter['exclude'])
                        is_sync = self.filter_check(src_relative_path, {
                            "contains": root_info['filter']['contains'],
                            "exclude": root_info['filter']['exclude']
                        })
                        if is_sync is False:
                            continue

                        if file['name'] in file_map:
                            if file_map[file['name']]['modify'] <= file['modify']:
                                is_upload = False
                                pretty("!", file['path'])
                            else:
                                pretty("=", file['path'])
                        else:
                            pretty("+", file['path'])
                        if is_upload:
                            self.on("modified", {
                                "isDir": False,
                                "srcPath": file['path']
                            })
            return True
        root_info = self.get_dir(data['srcPath'])
        #   ===============================================================
        #   全局筛选
        src_relative_path = self.srcDevice.path_relative(data['srcPath'])
        global_filter = self.DEV_CONFIG.get('global_filter')
        root_info['filter']['contains'].extend(global_filter['contains'])
        root_info['filter']['exclude'].extend(global_filter['exclude'])
        is_sync = self.filter_check(src_relative_path, {
            "contains": root_info['filter']['contains'],
            "exclude": root_info['filter']['exclude']
        })
        # 判断是否不执行同步操作
        if is_sync is False:
            print("Drop", src_relative_path)
            return None
        #   ===============================================================

        dst_relative_path = str(root_info['dst']).rstrip("/") + src_relative_path
        print("MAP PATH")
        print(src_relative_path, dst_relative_path)
        if name == "modified":
            if data['isDir'] is False:
                srcPath = data['srcPath']
                self.dstDevice.upload(path=dst_relative_path, file=self.srcDevice.read(srcPath))
        if name == "created":
            if data['isDir'] is False:
                srcPath = data['srcPath']
                self.dstDevice.upload(path=dst_relative_path, file=self.srcDevice.read(srcPath))
            else:
                self.dstDevice.mkdir(path=self.srcDevice.path_relative(data['srcPath']))
        if name == "moved":
            dstPath = data['dstPath']
            self.dstDevice.rename(dst_relative_path, self.srcDevice.path_relative(dstPath))
        if name == "deleted":
            self.dstDevice.delete(dst_relative_path)
