# coding:utf-8

import sqlite3
from loguru import logger
from configdef import configDictSqlTables

class SqliteManager:
    def __init__(self, dbName):
        self.dbName_ = dbName
        self.conn_ = sqlite3.connect(dbName)
        self.init()

    def __del__(self):
        self.conn_.close()

    # 初始化
    def init(self):
        logger.info("初始化数据库")
        listTables = self.select("sqlite_master", ["tbl_name"], "type='table'")

        if len(listTables) == 0:
            # 空数据库, 创建所有表
            for tblName, sql in configDictSqlTables.items():
                logger.info("创建表:{}", tblName)
                self.execute(sql)
        else:
            # 如果表不存在, 则创建表
            for row in listTables:
                tblName = row["tbl_name"]
                logger.info("检测表:{}", tblName)

        print(listTables)

    # 查询
    def select(self, tableName, selectColumn, where = ""):
        listResult = []
        try:
            sql = "select "
            colLength = len(selectColumn)
            for i in range(0, colLength):
                sql += selectColumn[i]
                if i != colLength - 1:
                    sql += ", "
            sql += " from '" + tableName + "'"
            if where != "":
                sql += " where " + where
            cursor = self.conn_.execute(sql)
            for row in cursor:
                dictData = {}
                for i in range(0, colLength):
                    dictData[selectColumn[i]] = row[i]
                listResult.append(dictData)

        except Exception as e:
            listResult = []
            logger.error(str(e))

        return listResult

    # 执行
    def execute(self, sql):
        try:
            self.conn_.execute(sql)
        except Exception as e:
            logger.error(str(e))
            return False
        return True

