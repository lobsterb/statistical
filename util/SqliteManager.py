# coding:utf-8

import sqlite3
from loguru import logger
from configdef import configDictSqlTables


class SqliteManager:
    def __init__(self, dbName):
        self.dbName_ = dbName
        self.conn_ = sqlite3.connect(dbName)
        self.initDb()

    def __del__(self):
        self.conn_.close()

    # 初始化
    def initDb(self):
        logger.info("初始化数据库")
        listResult = self.select("sqlite_master", ["tbl_name"], "type='table'")
        listTables = []
        for row in listResult:
            listTables.append(row["tbl_name"])

        for tblName, sql in configDictSqlTables.items():
            if tblName not in listTables:
                logger.info("创建表:{}", tblName)
                self.execute(sql)

    # 查询
    def select(self, tableName, selectColumn, where=""):
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
            cursor = self.conn_.cursor()
            cursor = cursor.execute(sql)
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
            cursor = self.conn_.cursor()
            cursor.execute(sql)
            self.conn_.commit()
        except Exception as e:
            logger.error(str(e))
            return False
        return True
