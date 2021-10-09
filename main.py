# coding:utf-8

import os
import shutil
import sys
import configparser

from logic import Logic
from loguru import logger

from configdef import configFuzzyMatching
from configdef import configRule


def notEmpty(s):
    return s and s.strip()


if __name__ == '__main__':
    os.system("chcp 65001")
    logger.add("logs/{time:YYYY-MM-DD}.log", rotation="5 MB", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
    # 检测程序所在文件夹中是否存在src目录, 输出目录为所在文件夹
    curDir = os.getcwd()
    srcDir = os.path.join(curDir, "src")
    if not os.path.exists(srcDir):
        logger.info("没有找到src目录, 请在当前目录中创建src文件夹,并将需要对比的数据拷贝到src文件夹中")
        os.system("pause")
        sys.exit(0)

    outDir = os.path.join(curDir, "out")
    if os.path.exists(outDir):
        logger.warning("检测到out目录,删除上次结果")
        shutil.rmtree(outDir)
        os.makedirs(outDir)

    # 读取配置文件
    configPath = os.path.join(curDir, "settings.ini")
    if not os.path.exists(configPath):
        logger.error("当前目录下没有settings.ini配置文件,无法继续执行")
        os.system("pause")
        sys.exit(0)

    field = ""
    certainty = ""
    unCertainty = ""
    unCertaintyCount = ""
    try:
        conf = configparser.ConfigParser()
        conf.read(configPath, encoding="utf8")
        secs = conf.sections()
        # FuzzyMatching, Rule
        # 获取模糊替换规则
        items = conf.items("FuzzyMatching")
        for item in items:
            configFuzzyMatching[item[0]] = item[1]

        field = conf.get("Rule", "Field", fallback="")
        certainty = conf.get("Rule", "Certainty", fallback="")
        unCertainty = conf.get("Rule", "UnCertainty", fallback="")
        unCertaintyCount = conf.get("Rule", "UnCertaintyCount", fallback=0)

        if field == "" or certainty == "" or unCertainty == "" or \
                unCertaintyCount == 0:
            raise Exception("匹配规则中,Field, Certainty, UnCertainty, UnCertaintyCount必要字段有空值")

    except Exception as e:
        logger.error("配置文件settings.ini内容格式错误:{}", str(e))
        os.system("pause")
        sys.exit(0)

    configRule["Field"] = field

    configRule["Certainty"] = certainty

    newList = unCertainty.split(",")
    for item in newList:
        configRule["UnCertainty"].add(item.strip())
    configRule["UnCertaintyCount"] = unCertaintyCount

    logger.info("当前脚本规则:")
    logger.info("属性必要字段:{}", configRule["Field"])
    logger.info("确定性匹配规则:{}", configRule["Certainty"])
    logger.info("不确定性匹配规则:{}", configRule["UnCertainty"])
    logger.info("不确定性匹配规则包含数量:{}", configRule["UnCertaintyCount"])

    logic = Logic(srcDir, outDir)
    logic.start()
    # os.system("pause")
