# coding:utf-8

class OneRecord:
    def __init__(self, name):
        self.name_ = name
        self.list_ = []


configDictSqlTables = {
    # 比对历史记录表, 将对比过的文件记录在这里
    "CompareHistory": """
        create table CompareHistory(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fileName text not null,
            md5 text not null
        );
    """,
    # 记录所有字段属性
    "FieldInfo": """
        create table FieldInfo(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fieldName text not null
        );
    """,
    # 用户信息
    "UserInfo": """
        create table UserInfo(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userName text not null,
            userId text not null,
            content text not null,
            fieldDesc text not null
        );
    """
}

configDictSql = {
    # 比对历史记录表, 将对比过的文件记录在这里
    "insertFieldInfo": """
        insert into 'FieldInfo' (fieldName) values('{}');
    """
}

configFuzzyMatching = {}
configRule = {"Field": "", "Certainty": "", "UnCertainty": set([]), "UnCertaintyCount": 0}
