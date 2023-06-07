import datetime
import ftplib
import os
import time
from abc import ABC, abstractmethod
from ftplib import FTP, error_perm
import re


class TransmitBase(ABC):
    name: str = ""

    def __init__(self, config: dict):
        self.config = config
        print("[载入" + self.name + "配置]", self.config)

    @abstractmethod
    def upload(self, path, fp) -> bool:
        """上传文件"""
        pass

    @abstractmethod
    def read(self, filename):
        """读取文件"""
        pass

    @abstractmethod
    def mkdir(self, path) -> bool:
        """创建目录"""
        return False

    @abstractmethod
    def unlink(self, path) -> bool:
        """移除目录"""
        return False

    @abstractmethod
    def rename(self, name, newname) -> bool:
        """重命名文件/目录"""
        return False

    @abstractmethod
    def delete(self, filename: str) -> bool:
        """删除文件"""
        return False

    @abstractmethod
    def move(self, src_path, dst_path) -> bool:
        """移动文件"""
        return False

    def all_directory(self, src_path):
        pass


class LocalDrive(TransmitBase):
    root: str = "/"

    def move(self, src_path, dst_path) -> bool:
        pass

    def delete(self, filename: str) -> bool:
        pass

    def rename(self, name, newname) -> bool:
        pass

    def upload(self, path, fp) -> bool:
        pass

    def __init__(self, root="/"):
        self.name = "本地传输驱动"
        super().__init__({"root": root})
        self.root = root
        pass

    def read(self, filename):
        return open(filename, 'rb')

    def mkdir(self, path) -> bool:
        os.mkdir(path)
        return True

    def unlink(self, path):
        os.unlink(path)

    def remove(self, filename):
        os.remove(filename)

    def save(self, filename):
        pass

    def lists(self, path):
        path = self.root + path
        return os.listdir(path)

    def all_directory(self, path: str = ""):
        path = self.root + path
        return [x[0] for x in os.walk(path)]

    def info(self, path: str):
        f_name = os.path.basename(path)
        f_type = "file"
        if os.path.isdir(path):
            f_type = "dir"
        f_size = os.path.getsize(path)
        f_mtime = int(os.path.getmtime(path))
        return {'path': path, 'name': f_name, 'type': f_type, 'sizd': f_size, 'modify': f_mtime, 'UNIX.mode': '',
                'UNIX.uid': '', 'UNIX.gid': '', 'unique': ''}



class FtpDrive(TransmitBase):
    def move(self, src_path, dst_path) -> bool:
        pass

    def read(self, filename):
        pass

    def __init__(self, host, port=21, username="", password="", root="/"):
        self.name = "Ftp传输驱动"
        super().__init__({
            "host": host,
            "port": port,
            "timeout": 10,
            "source_address": None,
            "user": username,
            "passwd": password,
            "acct": "",
            "root": root
        })

        self.ftp_ = FTP()
        self.connect()
        self.ftp_root = "/" + str(self.config['root']).lstrip("/")
        # 切换到根目录
        self.root()

    def connect(self):
        self.ftp_.connect(
            host=self.config.get('host'),
            port=self.config.get('port'),
            timeout=self.config.get('timeout'),
            source_address=self.config.get('source_address')
        )
        self.ftp_.login(
            user=self.config.get('user'),
            passwd=self.config.get('passwd'),
            acct=self.config.get('acct')
        )
        print(self.ftp_.welcome)
        # self.close_connect()
        # self.path_list("/")

    def close_connect(self):
        print("关闭FTP")
        self.ftp_.close()

    def path_list(self, path: str) -> list:
        """
        获取路径信息
        :param path: 路径
        :return:
        """
        # 获取 ftp
        ftp = self.ftp_
        # 切换路径
        ftp.cwd(path)
        # 显示目录下所有目录信息
        ftp.dir()
        # 获取目录下的文件夹
        dir_list: list = ftp.nlst()
        # 排序
        dir_list.sort()
        return dir_list

    def root(self):
        self.ftp_.cwd("~")
        try:
            self.ftp_.cwd(self.ftp_root)
        except Exception as e:
            if "No such file or directory" in e.args[0]:
                self.ftp_.mkd(self.ftp_root)
                self.ftp_.cwd(self.ftp_root)
                return None
            print("[切换根目录出错]", e.args)

    def auth(self, path: str):
        path = self.ftp_root + path
        print("PATH", path)
        self.ftp_.sendcmd('SITE CHMOD 655 ' + path)

    def upload(self, filename: str, fp, retry: int = 0):
        if retry >= 3:
            return False
        """
        上传文件
        :param retry: 
        :param filename:
        :param fp:
        :return:
        """
        path = self.ftp_root + filename
        try:
            self.ftp_.storbinary('STOR ' + path, fp)
            return True
        except TimeoutError as e:
            # 超时重新连接
            self.connect()
            # 重新上传
            return self.upload(filename=filename, fp=fp, retry=retry + 1)
        except ftplib.error_perm as e:
            if e.args[0] == "553 Can't open that file: No such file or directory":
                self.mkdir(os.path.dirname(filename))
                return self.upload(filename=filename, fp=fp, retry=retry + 1)

    def mkdir(self, path: str) -> bool:
        path = self.ftp_root + path
        path = path.replace("\\", "/")
        path = path.lstrip("\\")

        def create(name):
            try:
                return self.ftp_.mkd(name)
            except Exception as e:
                if e.args[0] == "550 Can't create directory: File exists":
                    return True
                return False

        for _dir in path.split("\\"):
            r = create(name=_dir)
            if r is False:
                return False
            self.ftp_.cwd(_dir)
        return True

    def unlink(self, path: str) -> bool:
        path = self.ftp_root + path
        try:
            self.ftp_.rmd(path)
            return True
        except Exception as e:
            if "No such file or directory" in e.args[0]:
                return True
            print("[目录删除失败]", e.args)
            return False

    def rename(self, src_path, dst_path) -> bool:
        src_path = self.ftp_root + src_path
        dst_path = self.ftp_root + dst_path
        try:
            self.ftp_.sendcmd('RNFR ' + src_path)
        except Exception as e:
            print("[文件移动/重命名失败]", e.args)
            if "but that file doesn't exist" in e.args[0]:
                # 源文件不存在
                pass
            return False
        self.ftp_.voidcmd('RNTO ' + dst_path)
        return True

    def delete(self, filename: str) -> bool:
        """删除文件
        :param filename:
        :return:
        """
        filename = self.ftp_root + filename
        try:
            self.ftp_.delete(filename=filename)
            print("[TRANSMIT-EVENT] CMD# DELETE FTP FILE: {0}".format(filename))
            return True
        except Exception as e:
            print("[TRANSMIT-EVENT] CMD# DELETE FTP FILE ERROR: ", e.args)
            return False

    def copy(self, src_path, dst_path) -> bool:
        return False

    def getdirs(self, dir_path=None):
        """
        获取当前路径或者指定路径下的文件、目录
        :param dir_path:
        :param args:
        :return:
        """
        if dir_path != None:
            self.ftp_.cwd(dir_path)
        dir_list = []
        self.ftp_.dir('.', dir_list.append)
        dir_name_list = [dir_detail_str.split(' ')[-1] for dir_detail_str in dir_list]
        return [file for file in dir_name_list if file != "." and file != ".."]

    def checkFileDir(self, dir_path):
        """
        检查指定路径是目录还是文件
        :param dir_path: 文件路径或目录路径
        :return:返回字符串“File”为文件，“Dir”问文件夹，“Unknow”为无法识别
        """
        rec = ""
        try:
            rec = self.ftp_.cwd(dir_path)  # 需要判断的元素
            self.ftp_.cwd("..")  # 如果能通过路劲打开必为文件夹，在此返回上一级
        except error_perm as fe:
            rec = fe  # 不能通过路劲打开必为文件，抓取其错误信息
        finally:
            if "Not a directory" in str(rec):
                return "File"
            elif "Current directory is" in str(rec):
                return "Dir"
            else:
                return "Unknow"

    def lists(self, path: str = "") -> list:
        path = str(self.ftp_root + path)
        """
        查询目录下的文件列表
        :param path:
        :return:
        """
        self.ftp_.cwd(path)
        detail_list = []
        self.ftp_.retrlines('MLSD', detail_list.append)
        data = []
        for str_ in detail_list:
            item = {}
            for val_ in str_.split(";"):
                val_ = val_.split("=")
                if len(val_) == 2:
                    if val_[0] == 'modify':
                        # 转换成时间数组
                        y = val_[1][0:4] + "-" + val_[1][4:6] + "-" + val_[1][6:8]
                        t = val_[1][8:10] + ":" + val_[1][10:12] + ":" + val_[1][12:]
                        timeArray = time.strptime(y + " " + t, "%Y-%m-%d %H:%M:%S")
                        # 转换成时间戳
                        val_[1] = int(time.mktime(timeArray))
                    item[val_[0]] = val_[1]
                else:
                    item['name'] = val_[0][1:]
            if item['name'] == "." or item['name'] == "..":
                continue
            data.append(item)
        return data
