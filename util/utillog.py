# coding:utf-8
# 初始化日志信息

import os
import shutil
import util.log
import time

logger = util.log.logger


def initLog():
    # 初始化log
    cur_time = str(int(round(time.time() * 1000)))
    cur_dir = os.path.join(os.getcwd(), "logs")

    # 如果是本地版本, 删除日志文件
    local = os.path.join(os.getcwd(), "local")
    if os.path.exists(local):
        shutil.rmtree(cur_dir, ignore_errors=True)

    log_file = "{}.log".format(os.path.join(cur_dir, cur_time))
    if not os.path.exists(cur_dir):
        os.makedirs(cur_dir)

    if os.path.exists(log_file):
        os.remove(log_file)

    util.log.init(log_file, "utf-8")
    return util.log.logger
