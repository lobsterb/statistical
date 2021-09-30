# coding:utf-8

import os
import shutil
import sys

from logic import Logic
from loguru import logger

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

    logic = Logic(srcDir, outDir)
    logic.start()
    os.system("pause")
