# coding:utf-8

import os
import shutil
import sys
import argparse
from util.utillog import initLog
from logic import Logic

logger = initLog()

if __name__ == '__main__':
    logDir = os.path.join(os.getcwd(), "logs")
    # if os.path.exists(logDir):
    #     shutil.rmtree(logDir, ignore_errors=True)

    inputDir = None
    outputDir = None

    parser = argparse.ArgumentParser(description="统计工具")
    parser.add_argument("--inputDir", "-i", required=True, type=str, help="存放统计文件的目录")
    parser.add_argument("--outputDir", "-o", required=True, type=str, help="存放结果文件的目录")
    args = parser.parse_args()

    if args.inputDir is None or args.outputDir is None:
        logger.error("参数错误")
        sys.exit()

    logic = Logic(args.inputDir, args.outputDir)
    logic.start()

    # input("按任意键结束")
