# coding:utf-8
import os
import time
import pandas

from util.utillog import logger
from util.xlsxreader import XlsxReader
from util.xlsxwriter import XlsxWriter


class Logic:
    def __init__(self, inputDir, outputDir):
        self.inputDir_ = inputDir
        self.outputDir_ = outputDir
        self.refactorDir = os.path.join(self.outputDir_, str(int(round(time.time() * 1000))))
        self.flag_ = "姓名"  # 必须要有的字段, 没有则不记录该条数据
        self.unionHeaders_ = []  # 所有格式的header并集, 整理文件统一格式用
        self.dictData_ = {}  # 存放所有人员信息
        self.refactorLimit_ = 100000
        self.refactorFileMaxRow_ = self.refactorLimit_  # 重构文件最大的行数
        self.refactorFileRow_ = 1  # 重构文件行数
        self.dictRefactorFiles_ = {}

    def start(self):
        logger.info("输入目录:{}, 输出目录:{}".format(self.inputDir_, self.outputDir_))
        listFiles = self.getAllFileList()
        fileCounts = len(listFiles)
        if fileCounts == 0:
            logger.error("没有找到任何文件")
            return

        # 读取文件内容
        logger.info("找到文件:{}个, 开始读取内容".format(fileCounts))
        for path in listFiles:
            try:
                reader = XlsxReader(path)
                sheetNames = reader.getSheetNames()

                logger.info("读取文件:{}".format(path))
                for sheet in sheetNames:
                    logger.info("读取sheet:{}".format(sheet))
                    reader.openSheet(sheet)
                    listHeaders = reader.getSheetHeader(sheet)
                    headerLen = len(listHeaders)
                    if headerLen == 0:
                        logger.warn("文件:{}, sheet:{}, 列头长度为0".format(path, sheet))
                        continue

                    # 求并集
                    self.unionHeaders_ = list(set(listHeaders).union(set(self.unionHeaders_)))

                    while True:
                        record = reader.getOneRecord(listHeaders)
                        if len(record) == 0:
                            break

                        # 每条记录中必须要有姓名的字段, 否在无法去重
                        if self.flag_ in record.keys():
                            flag = record[self.flag_]
                            if flag in self.dictData_.keys():
                                self.dictData_[flag].append(record)
                            else:
                                listData = [record]
                                self.dictData_[flag] = listData

            except Exception as e:
                logger.error(str(e))

        # 所有数据读取完毕, 重新构建文件
        self.refactorFiles()

        # 读取重构文件并筛重
        self.filterData()

        # 去重重构文件
        self.dropDuplicates()

    def dropDuplicates(self):
        for path, newPath in self.dictRefactorFiles_.items():
            data = pandas.read_excel(path)
            data = data.drop_duplicates(subset=["姓名", "身份证"], keep="first")
            print(data)
            data.to_excel(newPath, encoding="utf-8", index=True)

    def filterData(self):
        dictFilter = {}
        for p in os.listdir(self.refactorDir):
            fileName, extName = os.path.splitext(p)
            if "重构文件" in fileName and extName == ".xlsx":
                fullPath = os.path.join(self.refactorDir, p)
                logger.info("读取重构文件:{}".format(fullPath))
                reader = XlsxReader(fullPath)
                sheetNames = reader.getSheetNames()
                for sheet in sheetNames:
                    reader.openSheet(sheet)
                    listHeaders = reader.getSheetHeader(sheet)

                    while True:
                        data = reader.getOneRecord(listHeaders)
                        if len(data) == 0:
                            break

                        flag = data[self.flag_]

                        if flag in dictFilter.keys():
                            dictFilter[flag].append(data)
                        else:
                            listData = [data]
                            dictFilter[flag] = listData

        limit = 100000

        dataStartRow = 1
        dataMaxRow = limit
        dataRow = 1

        repeatDataStartRow = 1
        repeatMaxRow = limit
        repeatDataRow = 1

        writer = XlsxWriter(self.unionHeaders_)
        writer.writeHeader()

        repeatWriter = XlsxWriter(self.unionHeaders_)
        repeatWriter.writeHeader()

        for name, listData in dictFilter.items():
            if len(listData) > 1:
                # 把重复的数据单独输出到一个文件中
                for data in listData:
                    repeatWriter.writeData(data)
                    repeatDataRow += 1
                    if repeatDataRow > repeatMaxRow:
                        outFile = os.path.join(self.outputDir_,
                                               "重复数据_{}_{}.xlsx".format(repeatDataStartRow, repeatDataRow - 1))
                        repeatWriter.save(outFile)
                        logger.info("保存重复文件:{}".format(outFile))
                        repeatDataStartRow = repeatDataRow

                        repeatMaxRow += limit
                        repeatWriter = XlsxWriter(outFile, self.unionHeaders_)
                        repeatWriter.writeHeader()
                # 只保留一条数据, 并写入到不重复的数据中

            else:
                writer.writeData(listData[0])
                dataRow += 1
                if dataRow > dataMaxRow:
                    outFile = os.path.join(self.outputDir_,
                                           "不重复数据_{}_{}.xlsx".format(dataStartRow, dataRow - 1))
                    writer.save(outFile)
                    logger.info("保存不重复文件:{}".format(outFile))
                    dataStartRow = dataRow

                    dataMaxRow += limit
                    writer = XlsxWriter(outFile, self.unionHeaders_)
                    writer.writeHeader()

        outFile = os.path.join(self.refactorDir,
                               "不重复数据_{}_{}.xlsx".format(dataStartRow, dataRow - 1))
        writer.save(outFile)

        outFile = os.path.join(self.refactorDir,
                               "重复数据_{}_{}.xlsx".format(repeatDataStartRow, repeatDataRow - 1))
        repeatWriter.save(outFile)

    def refactorFiles(self):
        logger.info("重新组建文件结构, 重构文件输出目录:{}".format(self.refactorDir))
        if not os.path.exists(self.refactorDir):
            os.makedirs(self.refactorDir)

        startRow = self.refactorFileRow_
        writer = XlsxWriter(self.unionHeaders_)
        writer.writeHeader()

        for name, listData in self.dictData_.items():
            for data in listData:

                # 没有标志位
                if self.flag_ not in data.keys():
                    continue

                # 标志位无效
                flag = data[self.flag_]
                if flag == "None" or flag == "姓名":
                    continue

                writer.writeData(data)
                self.refactorFileRow_ += 1
                if self.refactorFileRow_ > self.refactorFileMaxRow_:
                    outFile = os.path.join(self.refactorDir,
                                           "重构文件_{}_{}.xlsx".format(startRow, self.refactorFileRow_ - 1))

                    filterOutFile = os.path.join(self.refactorDir,
                                                 "去重重构文件_{}_{}.xlsx".format(startRow, self.refactorFileRow_ - 1))
                    writer.save(outFile)
                    self.listRefactorFiles_[outFile] = filterOutFile

                    logger.info("保存重构文件:{}".format(outFile))
                    startRow = self.refactorFileRow_

                    self.refactorFileMaxRow_ += self.refactorLimit_
                    writer = XlsxWriter(outFile, self.unionHeaders_)
                    writer.writeHeader()

        outFile = os.path.join(self.refactorDir,
                               "重构文件_{}_{}.xlsx".format(startRow, self.refactorFileRow_ - 1))
        writer.save(outFile)
        filterOutFile = os.path.join(self.refactorDir,
                                     "去重重构文件_{}_{}.xlsx".format(startRow, self.refactorFileRow_ - 1))
        self.dictRefactorFiles_[outFile] = filterOutFile

    # 获取文件列表
    def getAllFileList(self):
        listFiles = []
        # 判断目录是否存在
        if not os.path.exists(self.inputDir_):
            logger.error("存放统计文件的目录不存在")
            return listFiles

        for p in os.listdir(self.inputDir_):
            if p.startswith("~$"):
                continue
            filePath = os.path.join(self.inputDir_, p)
            listFiles.append(filePath)
        return listFiles
