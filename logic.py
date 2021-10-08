# coding:utf-8

import os
import sys

from loguru import logger
from util.SqliteManager import SqliteManager
from util.CompareFile import CompareFile

from configdef import configDictSql
from configdef import configFuzzyMatching
from configdef import configRule


class Logic:
    def __init__(self, srcDir, outDir):
        self.srcDir_ = srcDir  # 比对文件目录
        self.outDir_ = outDir  # 输出目录
        self.db_ = SqliteManager("data.db")  # 数据库管理器

    def __del__(self):
        pass

    def start(self):
        logger.info("开始比对文件, 比对目录:{}", self.srcDir_)
        # 查找所有文件
        listFiles = []
        self.traverseDir(self.srcDir_, listFiles)
        if len(listFiles) == 0:
            logger.error("{}, 目录中没有文件", self.srcDir_)
            return

        for file in listFiles:
            try:
                # 读取文件内容
                compareFile = CompareFile(file)
                # 处理文件内容
                self.handleData(compareFile)

            except Exception as e:
                logger.error("处理文件错误:{}, 错误内容:{}", file, str(e))

    def traverseDir(self, targetDir, listFiles):
        for p in os.listdir(targetDir):
            fullPath = os.path.join(targetDir, p)
            if os.path.isdir(fullPath):
                self.traverseDir(fullPath, listFiles)
            else:
                fileName, extName = os.path.splitext(p)
                if not fileName.startswith("~$") and extName == ".xlsx":
                    listFiles.append(fullPath)

    def handleData(self, compareFile):
        for sheet in compareFile.sheets_:
            name = sheet.sheetName_
            listHeader = sheet.sheetHeader_
            listData = sheet.sheetData_

            logger.info("处理数据, sheet:{}", name)

            # 创建新的字段类型
            dictFieldInfo = self.createField(listHeader)
            if len(dictFieldInfo) == 0:
                logger.error("没有可用的字段, 程序退出")
                sys.exit(0)

            # 处理数据
            for data in listData:
                # 检测该数据是否有必要属性
                if not self.checkDataValid(data):
                    continue

                # 替换模糊匹配字段
                data = self.replaceField(data)

                # 保存数据
                self.saveData2Db(data)

    def saveData2Db(self, data):
        field = configRule["Field"]
        certainty = configRule["Certainty"]
        setUnCertainty = configRule["UnCertainty"]
        unCertaintyCount = configRule["UnCertaintyCount"]

        # 判断是否有确定性的字段, 根据该字段做不同的去重处理
        if certainty in data.keys():
            listResult = self.searchCertaintyDataExists(field, certainty, data)
            if len(listResult) > 0:
                # 数据已经存在, 判断确定性字段是否相同
                print("数据已经存在, 判断确定性字段是否相同")
                pass
            else:
                # 插入新的数据
                print("插入新的数据")
                pass
        else:
            print("没有确定性字段")

    def searchCertaintyDataExists(self, field, certainty, data):
        tblName = "UserInfo"
        userName = data[field]
        userId = data[certainty]
        return self.db_.select(tblName, ["userName"], "userName='{}' and userId='{}'".format(userName, userId))

    @staticmethod
    def replaceField(data):
        newDict = {}
        for k, v in data.items():
            replaceValue = ""
            for rk, rv in configFuzzyMatching.items():
                if rk in k:
                    replaceValue = rv
                    break
            if replaceValue != "" and k != replaceValue:
                # 需要替换
                logger.info("数据:{}需要替换字段, 替换属性:{}, 替换为:{}", data, k, replaceValue)
                newDict[replaceValue] = v
            else:
                newDict[k] = v
        return newDict

    @staticmethod
    def checkDataValid(data):
        field = configRule["Field"]
        keys = data.keys()
        if field not in keys:
            # 数据无效
            logger.warning("无效的数据:{}, 缺少必要字段:{}", data, field)
            return False

        return True

    def searchField(self, field):
        tblName = "FieldInfo"
        listResult = self.db_.select(tblName, ["id", "fieldName"], "fieldName='{}'".format(field))
        if len(listResult) == 0:
            return None, None
        else:
            return listResult[0]["id"], listResult[0]["fieldName"]

    def createField(self, listHeader):
        logger.info("字段属性:{}", listHeader)
        # 查找FieldInfo表, 判断是否有相同字段

        dictFieldInfo = {}

        for field in listHeader:
            fieldId, fieldName = self.searchField(field)
            if fieldId is None and fieldName is None:
                # 该字段不存在, 新建字段, 并记录id
                logger.info("创建新的字段类型:{}", field)
                sql = configDictSql["insertFieldInfo"].format(field)
                if not self.db_.execute(sql):
                    logger.error("创建字段错误, 程序退出")
                    sys.exit(0)
                # 再次查询
                fieldId, fieldName = self.searchField(field)
                if fieldId is None and fieldName is None:
                    logger.error("查询字段id错误:{}, 程序退出", field)
                    sys.exit(0)
            dictFieldInfo[fieldName] = fieldId
        return dictFieldInfo
# class Logic:
#     def __init__(self, inputDir, outputDir):
#         self.inputDir_ = inputDir
#         self.outputDir_ = outputDir
#         self.refactorDir = os.path.join(self.outputDir_, str(int(round(time.time() * 1000))))
#         self.flag_ = "姓名"  # 必须要有的字段, 没有则不记录该条数据
#         self.idFlag_ = "身份"
#         self.unionHeaders_ = ["数据来源"]  # 所有格式的header并集, 整理文件统一格式用
#         self.dictFilter = {}  # 存放所有人员信息
#         self.refactorLimit_ = 100000
#         self.refactorFileMaxRow_ = self.refactorLimit_  # 重构文件最大的行数
#         self.refactorFileRow_ = 1  # 重构文件行数
#         self.dictRefactorFiles_ = {}
#
#     def start(self):
#         logger.info("输入目录:{}, 输出目录:{}".format(self.inputDir_, self.outputDir_))
#         listFiles = self.getAllFileList()
#         fileCounts = len(listFiles)
#         if fileCounts == 0:
#             logger.error("没有找到任何文件")
#             return
#
#         # 读取文件内容
#         logger.info("找到文件:{}个, 开始读取内容".format(fileCounts))
#         for path in listFiles:
#             try:
#                 reader = XlsxReader(path)
#                 sheetNames = reader.getSheetNames()
#
#                 logger.info("读取文件:{}".format(path))
#                 for sheet in sheetNames:
#                     logger.info("读取sheet:{}".format(sheet))
#                     reader.openSheet(sheet)
#                     listHeaders = reader.getSheetHeader(sheet)
#                     headerLen = len(listHeaders)
#                     if headerLen == 0:
#                         logger.warn("文件:{}, sheet:{}, 列头长度为0".format(path, sheet))
#                         continue
#
#                     # 求并集
#                     self.unionHeaders_ = list(set(listHeaders).union(set(self.unionHeaders_)))
#
#                     while True:
#                         record = reader.getOneRecord(listHeaders)
#                         if len(record) == 0:
#                             break
#
#                         # 每条记录中必须要有姓名的字段, 否在无法去重
#                         if self.flag_ in record.keys():
#                             flag = record[self.flag_]
#                             if flag in self.dictFilter.keys():
#                                 self.dictFilter[flag].append(record)
#                             else:
#                                 listData = [record]
#                                 self.dictFilter[flag] = listData
#
#             except Exception as e:
#                 logger.error(str(e))
#
#         # 所有数据读取完毕, 重新构建文件
#         self.refactorFiles()
#
#         # 读取重构文件并筛重
#         self.filterData()
#
#         # # 去重重构文件
#         # self.dropDuplicates()
#
#     def dropDuplicates(self):
#         for path, newPath in self.dictRefactorFiles_.items():
#             data = pandas.read_excel(path)
#             data = data.drop_duplicates(subset=["姓名", "身份证"], keep="first")
#             data.to_excel(newPath, encoding="utf-8", index=True)
#
#     def filterData(self):
#         dictFilter = {}
#         dictRepeat = {}
#         for p in os.listdir(self.refactorDir):
#             fileName, extName = os.path.splitext(p)
#             if "重构文件" in fileName and extName == ".xlsx":
#                 fullPath = os.path.join(self.refactorDir, p)
#                 logger.info("读取重构文件:{}".format(fullPath))
#                 reader = XlsxReader(fullPath)
#                 sheetNames = reader.getSheetNames()
#                 for sheet in sheetNames:
#                     reader.openSheet(sheet)
#                     listHeaders = reader.getSheetHeader(sheet)
#
#                     while True:
#                         record = reader.getOneRecord(listHeaders)
#                         if len(record) == 0:
#                             break
#
#                         flag = record[self.flag_]
#
#                         if flag in dictFilter.keys():
#                             listData = dictFilter[flag]
#                             isRepeat = False
#                             for oldRecord in listData:
#                                 recordId = ""
#
#                                 for key in record.keys():
#                                     if self.idFlag_ in key:
#                                         recordId = record[key]
#                                         break
#                                 for key in oldRecord.keys():
#                                     if self.idFlag_ in key:
#                                         oldId = oldRecord[key]
#                                         break
#                                 # 判断是否都有身份证的列, 如果有身份证, 并且数据不为None, 则按姓名, 身份证去重
#                                 if recordId != "None" and oldId != "None":
#                                     if recordId == oldId:
#                                         # 相同数据
#                                         isRepeat = True
#                                         break
#                                     else:
#                                         # 不重复
#                                         break
#
#                                 # 如果没有身份证信息, 则按除姓名外, 任意三列一样去重
#                                 repeatCount = 0
#                                 for header in self.unionHeaders_:
#                                     try:
#                                         if record[header] != "None" and oldRecord[header] != "None":
#                                             if record[header] == oldRecord[header]:
#                                                 repeatCount += 1
#                                                 if repeatCount >= 3:
#                                                     isRepeat = True
#                                                     break
#                                     except Exception as e:
#                                         logger.error(str(e))
#
#                                 if isRepeat:
#                                     break
#
#                             if not isRepeat:
#                                 dictFilter[flag].append(record)
#                             else:
#                                 if flag in dictRepeat.keys():
#                                     dictRepeat[flag].append(record)
#                                 else:
#                                     dictRepeat[flag] = [record]
#                         else:
#                             listData = [record]
#                             dictFilter[flag] = listData
#
#         limit = 100000
#
#         dataStartRow = 1
#         dataMaxRow = limit
#         dataRow = 1
#
#         repeatDataStartRow = 1
#         repeatMaxRow = limit
#         repeatDataRow = 1
#
#         writer = XlsxWriter(self.unionHeaders_)
#         writer.writeHeader()
#
#         repeatWriter = XlsxWriter(self.unionHeaders_)
#         repeatWriter.writeHeader()
#
#         for name, listData in dictFilter.items():
#             for record in listData:
#                 writer.writeData(record)
#                 dataRow += 1
#                 if dataRow > dataMaxRow:
#                     outFile = os.path.join(self.outputDir_,
#                                            "不重复数据_{}_{}.xlsx".format(dataStartRow, dataRow - 1))
#                     writer.save(outFile)
#                     logger.info("保存不重复文件:{}".format(outFile))
#                     dataStartRow = dataRow
#
#                     dataMaxRow += limit
#                     writer = XlsxWriter(outFile, self.unionHeaders_)
#                     writer.writeHeader()
#
#         for name, listData in dictRepeat.items():
#             # 把重复的数据单独输出到一个文件中
#             for record in listData:
#                 repeatWriter.writeData(record)
#                 repeatDataRow += 1
#                 if repeatDataRow > repeatMaxRow:
#                     outFile = os.path.join(self.outputDir_,
#                                            "重复数据_{}_{}.xlsx".format(repeatDataStartRow, repeatDataRow - 1))
#                     repeatWriter.save(outFile)
#                     logger.info("保存重复文件:{}".format(outFile))
#                     repeatDataStartRow = repeatDataRow
#
#                     repeatMaxRow += limit
#                     repeatWriter = XlsxWriter(outFile, self.unionHeaders_)
#                     repeatWriter.writeHeader()
#
#         outFile = os.path.join(self.refactorDir,
#                                "不重复数据_{}_{}.xlsx".format(dataStartRow, dataRow - 1))
#         writer.save(outFile)
#
#         outFile = os.path.join(self.refactorDir,
#                                "重复数据_{}_{}.xlsx".format(repeatDataStartRow, repeatDataRow - 1))
#         repeatWriter.save(outFile)
#
#     def refactorFiles(self):
#         logger.info("重新组建文件结构, 重构文件输出目录:{}".format(self.refactorDir))
#         if not os.path.exists(self.refactorDir):
#             os.makedirs(self.refactorDir)
#
#         startRow = self.refactorFileRow_
#         writer = XlsxWriter(self.unionHeaders_)
#         writer.writeHeader()
#
#         for name, listData in self.dictFilter.items():
#             for data in listData:
#
#                 # 没有标志位
#                 if self.flag_ not in data.keys():
#                     continue
#
#                 # 标志位无效
#                 flag = data[self.flag_]
#                 if flag == "None" or flag == "姓名":
#                     continue
#
#                 writer.writeData(data)
#                 self.refactorFileRow_ += 1
#                 if self.refactorFileRow_ > self.refactorFileMaxRow_:
#                     outFile = os.path.join(self.refactorDir,
#                                            "重构文件_{}_{}.xlsx".format(startRow, self.refactorFileRow_ - 1))
#
#                     filterOutFile = os.path.join(self.refactorDir,
#                                                  "去重重构文件_{}_{}.xlsx".format(startRow, self.refactorFileRow_ - 1))
#                     writer.save(outFile)
#                     self.listRefactorFiles_[outFile] = filterOutFile
#
#                     logger.info("保存重构文件:{}".format(outFile))
#                     startRow = self.refactorFileRow_
#
#                     self.refactorFileMaxRow_ += self.refactorLimit_
#                     writer = XlsxWriter(outFile, self.unionHeaders_)
#                     writer.writeHeader()
#
#         outFile = os.path.join(self.refactorDir,
#                                "重构文件_{}_{}.xlsx".format(startRow, self.refactorFileRow_ - 1))
#         writer.save(outFile)
#         filterOutFile = os.path.join(self.refactorDir,
#                                      "去重重构文件_{}_{}.xlsx".format(startRow, self.refactorFileRow_ - 1))
#         self.dictRefactorFiles_[outFile] = filterOutFile
#
#     # 获取文件列表
#     def getAllFileList(self):
#         listFiles = []
#         # 判断目录是否存在
#         if not os.path.exists(self.inputDir_):
#             logger.error("存放统计文件的目录不存在")
#             return listFiles
#
#         for p in os.listdir(self.inputDir_):
#             if p.startswith("~$"):
#                 continue
#             filePath = os.path.join(self.inputDir_, p)
#             listFiles.append(filePath)
#         return listFiles
