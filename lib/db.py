import json
import sqlite3
import time
import uuid

class LiteDb(object):
    _instance = None

    def __init__(self):
        self.cursor = None
        self.dbname = None
        self.conn = None
        self.table_prefix = ""

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def openDb(self, dbname, table_prefix=""):
        self.dbname = dbname
        self.table_prefix = table_prefix
        self.conn = sqlite3.connect(self.dbname)
        self.cursor = self.conn.cursor()

    def closeDb(self):
        """
        关闭数据库
        :return:
        """
        self.cursor.close()
        self.conn.close()

    def existTable(self, table: str):
        [_, res] = self.executeSql("SELECT name FROM sqlite_master WHERE type='table' and name='" + table + "'")
        return len(res) > 0

    def existData(self, table: str, where):
        [_, res] = self.executeSql("SELECT ID FROM " + table + " WHERE " + self.pares_where(where))
        return len(res) > 0

    def createTable(self, sql):
        """
        example：'create table userinfo(name text, email text)'
        :return: result=[1,None]
        """
        self.cursor.execute(sql)
        self.conn.commit()
        result = [1, None]
        return result

    def dropTable(self, table):
        """
        :param table:
        :return:result=[1,None]
        """
        self.cursor.execute("drop table " + self.pares_table(table))
        self.conn.commit()
        result = [1, None]
        return result

    def executeSql(self, sql, value=None):
        """
        执行单个sql语句，只需要传入sql语句和值便可
        :param sql:'insert into user(name,password,number,status) values(?,?,?,?)'
                    'delete from user where name=?'
                    'updata user set status=? where name=?'
                    'select * from user where id=%s'
        :param value:[(123456,123456,123456,123456),(123,123,123,123)]
                value:'123456'
                value:(123,123)
        :return:result=[1,None]
        """

        '''增、删、查、改'''
        if isinstance(value, list) and isinstance(value[0], (list, tuple)):
            for val in value:
                self.cursor.execute(sql, val)
            else:
                self.conn.commit()
                result = [1, self.cursor.fetchall()]
        else:
            '''执行单条语句：字符串、整型、数组'''
            if value:
                self.cursor.execute(sql, value)
            else:
                self.cursor.execute(sql)
            self.conn.commit()
            result = [1, self.cursor.fetchall()]
        return result

    def pares_table(self, table: str):
        return self.table_prefix + table

    def pares_where(self, where):
        where_sql = ""
        if isinstance(where, str):
            where_sql = where
        if isinstance(where, dict):
            array = []
            for filed in where:
                if isinstance(where[filed], str):
                    array.append(filed + '=\'' + where[filed] + '\'')
            where_sql = " and ".join(array)
        return where_sql

    def delete(self, table, where: str, value=None):
        return self.executeSql("delete from " + self.pares_table(table) + " where " + self.pares_where(where), value)

    def insert(self, table, data: dict, mode: str = "II"):
        filed = ",".join(data.keys())
        values = ",".join(['?'] * len(data.keys()))
        modes = {
            # 正常的插入数据，插入数据的时候会检查主键或者唯一索引，如果出现重复就会报错；
            'II': 'insert into',
            # 表示插入并替换数据，若表中有primary key或者unique索引，在插入数据的时候，若遇到重复的数据，则用新数据替换，如果没有数据效果则和insert into一样；
            'RI': 'replace into',
            # 插入并忽略数据，如果中已经存在相同的记录，则忽略当前新数据。这样不用校验是否存在了，有则忽略，无则添加
            'III': 'insert ignore into'
        }
        sql = modes[mode]

        return self.executeSql(sql + " " + self.pares_table(table) + "(" + filed + ") values(" + values + ")",
                               list(data.values()))

    def select(self,
               table: str,
               fields: str | list = "*",
               where="1=1",
               value=None,
               limit: str = "limit 10",
               order: str = ""):
        if isinstance(fields, list):
            fields = ",".join(fields)
        [_, res] = self.executeSql(
            "select " + fields + " from " + table + " where " + self.pares_where(where) + " " + limit + " " + order,
            value)
        return self.pares_values(res, table, fields)

    def pares_values(self, rows, table, fields="*"):
        array = []
        for item in rows:
            if table == "watch_service" and fields == "*":
                array.append({
                    'ID': item[0],
                    'UUID': item[1],
                    'NAME': item[2],
                    'DEV_TYPE': item[3],
                    'DEV_CONFIG': json.loads(item[4]),
                    'SYNC_TYPE': item[5],
                    'TIMEER_CONFIG': json.loads(item[6]),
                    'SYNC_DIR': json.loads(item[7]),
                    'SORT_BY': item[8],
                    'RECYCLE_OPEN': item[9],
                    'RECYCLE_CONFIG': item[10]
                })
                continue
        if len(array) > 0:
            return array
        return rows

    def find(self,
             table: str,
             fields: str | list = "*",
             where="1=1",
             value=None,
             order: str = ""):
        res = self.select(table, fields, where, value, "limit 1", order)
        if len(res) == 1:
            return res[0]
        return None

    def delete_watch_service(self, where):
        return self.delete("watch_service", where)

    def save_watch_service(self, NAME, DEV_TYPE, DEV_CONFIG, SYNC_TYPE, TIMEER_CONFIG, SYNC_DIR, SORT_BY: int = 100,
                           RECYCLE_OPEN: int = 0, RECYCLE_CONFIG=None):
        if RECYCLE_CONFIG is None:
            RECYCLE_CONFIG = {}
        UUID = str(uuid.uuid1())
        res = self.insert('watch_service', {
            "UUID": UUID,
            "NAME": NAME,  # 服务名称
            "DEV_TYPE": DEV_TYPE,  # 驱动类型
            "DEV_CONFIG": json.dumps(DEV_CONFIG),  # 驱动配置
            "SYNC_TYPE": SYNC_TYPE,  # 同步方式 ( 10实时同步, 20定时同步, 30手动同步)
            "TIMEER_CONFIG": json.dumps(TIMEER_CONFIG),  # 定时同步配置
            "SYNC_DIR": json.dumps(SYNC_DIR),  # 同步目录映射关系
            "ADD_TIME": int(time.time()),  # 服务创建时间
            "STATUS": 0,  # 服务状态  ( 0未开启， 1已开启)
            "SORT_BY": SORT_BY,  # 排序号
            "RECYCLE_OPEN": RECYCLE_OPEN,  # 是否启用回收站功能 - 会产生大量日志记录和备份数据
            "RECYCLE_CONFIG": json.dumps(RECYCLE_CONFIG),  # 回收站配置
        })
        return [UUID, res]
