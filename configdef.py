# coding:utf-8

class OneRecord:
    def __init__(self, name):
        self.name_ = name
        self.list_ = []

configDictSqlTables = {
    "CompareHistory": """
        create table CompareHistory(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fileName text not null,
            md5 text not null
        );
    """}