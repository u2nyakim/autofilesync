from watchdog.events import *


class FileEventHandler(FileSystemEventHandler):

    def __init__(self, trigger):
        # 触发器
        self.trigger = trigger
        # 是否打印控制台日志
        self.printConsoleLog = True
        FileSystemEventHandler.__init__(self)

    def trigger_on(self, event: str, data: dict):
        if self.trigger:
            self.trigger.on(event, data)
        return True

    def on_moved(self, event):
        if self.printConsoleLog:
            if event.is_directory:
                print("directory moved from {0} to {1}".format(event.src_path, event.dest_path))
            else:
                print("file moved from {0} to {1}".format(event.src_path, event.dest_path))
        self.trigger_on('moved', {
            "isDir": event.is_directory,
            "srcPath": event.src_path,
            "dstPath": event.dest_path
        })

    def on_created(self, event):
        if self.printConsoleLog:
            if event.is_directory:
                print("directory created:{0}".format(event.src_path))
            else:
                print("file created:{0}".format(event.src_path))
        self.trigger_on('created', {
            "isDir": event.is_directory,
            "srcPath": event.src_path
        })

    def on_deleted(self, event):
        if self.printConsoleLog:
            if event.is_directory:
                print("directory deleted:{0}".format(event.src_path))
            else:
                print("file deleted:{0}".format(event.src_path))
        self.trigger_on('deleted', {
            "isDir": event.is_directory,
            "srcPath": event.src_path
        })

    def on_modified(self, event):
        if self.printConsoleLog:
            if event.is_directory:
                print("directory modified:{0}".format(event.src_path))
            else:
                print("file modified:{0}".format(event.src_path))
            # self.service.uploadFile(event.src_path)
        self.trigger_on('modified', {
            "isDir": event.is_directory,
            "srcPath": event.src_path
        })
