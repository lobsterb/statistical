# coding:utf-8

import os
import sys
import json
import re

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
        self.dictField_ = {}

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
                compareFile = CompareFile(file, self.checkHandleFile)

                # 判断文件是否处理过
                if not compareFile.isHandle_:
                    # 处理文件内容
                    self.handleData(compareFile)

            except Exception as e:
                logger.error("处理文件错误:{}, 错误内容:{}", file, str(e))

    def checkHandleFile(self, filePath, md5):
        listResult = self.db_.select("CompareHistory", ["md5"],
                                     "md5='{}'".format(md5))
        if len(listResult) > 0:
            logger.warning("文件:{}, 数据已经处理过, 跳过该文件", filePath)
            return True

        return False


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

            logger.info("处理sheet:{}", name)

            # 创建新的字段类型
            self.createField(listHeader)
            if len(self.dictField_) == 0:
                logger.error("没有可用的字段, 程序退出")
                sys.exit(0)

            # 处理数据
            for data in listData:
                logger.info("处理数据:{}", data)

                # 检测该数据是否有必要属性
                if not self.checkDataValid(data):
                    continue

                # 替换模糊匹配字段
                data = self.replaceField(data)

                # 保存数据
                self.saveData2Db(data)

            # 单文件处理完成, 记录文件md5
            # self.saveHandleFile(compareFile)

    def saveHandleFile(self, compareFile):
        filePath = compareFile.filePath_
        md5 = compareFile.md5_
        sql = "insert into 'CompareHistory'(fileName, md5) VALUES('{}', '{}')".format(filePath, md5)
        if not self.db_.execute(sql):
            logger.warning("记录处理文件错误:{}, md5:{}", filePath, md5)


    @staticmethod
    def checkIdCard(idCard):

        Errors = ['验证通过!', '身份证号码位数不对!', '身份证号码出生日期超出范围或含有非法字符!', '身份证号码校验错误!', '身份证地区非法!']
        area = {"11": "北京", "12": "天津", "13": "河北", "14": "山西", "15": "内蒙古", "21": "辽宁", "22": "吉林", "23": "黑龙江",
                "31": "上海", "32": "江苏", "33": "浙江", "34": "安徽", "35": "福建", "36": "江西", "37": "山东", "41": "河南",
                "42": "湖北", "43": "湖南", "44": "广东", "45": "广西", "46": "海南", "50": "重庆", "51": "四川", "52": "贵州",
                "53": "云南", "54": "西藏", "61": "陕西", "62": "甘肃", "63": "青海", "64": "宁夏", "65": "新疆", "71": "台湾",
                "81": "香港", "82": "澳门", "91": "国外"}
        idCard = str(idCard)
        idCard = idCard.strip()
        listIdCard = list(idCard)

        # 地区校验
        f = idCard[0:2]
        if f not in area.keys():
        #if not area[f]:
            return Errors[4]
        # 15位身份号码检测
        if len(idCard) == 15:
            if ((int(idCard[6:8]) + 1900) % 4 == 0 or (
                    (int(idCard[6:8]) + 1900) % 100 == 0 and (int(idCard[6:8]) + 1900) % 4 == 0)):
                erg = re.compile(
                    '[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}$')  # //测试出生日期的合法性
            else:
                ereg = re.compile(
                    '[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))[0-9]{3}$')  # //测试出生日期的合法性
            if (re.match(ereg, idCard)):
                return Errors[0]
            else:
                return Errors[2]
        # 18位身份号码检测
        elif (len(idCard) == 18):
            # 出生日期的合法性检查
            # 闰年月日:((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))
            # 平年月日:((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))
            if (int(idCard[6:10]) % 4 == 0 or (int(idCard[6:10]) % 100 == 0 and int(idCard[6:10]) % 4 == 0)):
                ereg = re.compile(
                    '[1-9][0-9]{5}(19[0-9]{2}|20[0-9]{2})((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}[0-9Xx]$')  # //闰年出生日期的合法性正则表达式
            else:
                ereg = re.compile(
                    '[1-9][0-9]{5}(19[0-9]{2}|20[0-9]{2})((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))[0-9]{3}[0-9Xx]$')  # //平年出生日期的合法性正则表达式
            # //测试出生日期的合法性
            if (re.match(ereg, idCard)):
                # //计算校验位
                S = (int(listIdCard[0]) + int(listIdCard[10])) * 7 + (
                            int(listIdCard[1]) + int(listIdCard[11])) * 9 + (
                                int(listIdCard[2]) + int(listIdCard[12])) * 10 + (
                                int(listIdCard[3]) + int(listIdCard[13])) * 5 + (
                                int(listIdCard[4]) + int(listIdCard[14])) * 8 + (
                                int(listIdCard[5]) + int(listIdCard[15])) * 4 + (
                                int(listIdCard[6]) + int(listIdCard[16])) * 2 + int(listIdCard[7]) * 1 + int(
                    listIdCard[8]) * 6 + int(listIdCard[9]) * 3
                Y = S % 11
                M = "F"
                JYM = "10X98765432"
                M = JYM[Y]  # 判断校验位
                if (M == listIdCard[17]):  # 检测ID的校验位
                    return Errors[0]
                else:
                    return Errors[3]
            else:
                return Errors[2]
        else:
            return Errors[1]

    def checkCertaintyVaild(self, data, mode=1):
        if data is None:
            return False

        if mode == 1:
            ret = self.checkIdCard(data)
            if ret == "验证通过!":
                return True
            else:
                logger.warning("{}:{}", ret, data)
        return False

    def saveData2Db(self, data):
        field = configRule["Field"]
        certainty = configRule["Certainty"]

        # 判断是否有确定性的字段, 根据该字段做不同的去重处理
        if certainty in data.keys():

            if self.checkCertaintyVaild(data[certainty]):
                listResult = self.searchCertaintyDataExists(field, certainty, data)
                if len(listResult) > 0:
                    # 数据已经存在, 判断确定性字段是否相同
                    self.appendData(certainty, data)
                else:
                    # 插入新的数据
                    self.insertData(field, data, certainty)
            else:
                logger.warning("处理无效:<{}>的数据,{}", certainty, data)
                self.handleUncertaintyData(field, data)
        else:
            logger.warning("处理没有:<{}>的数据,{}", certainty, data)
            self.handleUncertaintyData(field, data)

    def checkUnCertaintyDataExists(self, field, data):
        tblName = "UserInfo"
        userName = data[field]
        if userName is None or userName == "" or userName == "None":
            return []
        return self.db_.select(tblName, ["id","userName","userId","content","fieldDesc"], "userName='{}'".format(userName))

    def handleUncertaintyData(self, field, data):

        listResult = self.checkUnCertaintyDataExists(field, data)
        if len(listResult) > 0:
            # 判断数据是否存在
            self.compareData(data, listResult)
        else:
            # 插入一条数据
            self.insertData(field, data)

    def compareData(self, data, listResult):
        setUnCertainty = configRule["UnCertainty"]
        unCertaintyCount = configRule["UnCertaintyCount"]

        for userInfo in listResult:
            print(userInfo)

    # 完善数据, 补齐数据
    def appendData(self, certainty, data):
        userId = data[certainty]
        newFieldDesc = self.getFieldDesc(data)
        newFieldDesc = [str(x) for x in newFieldDesc]
        newFieldDesc.sort()
        newContent = data

        # 查询已经存在的记录
        listResult = self.db_.select("UserInfo", ["userName", "userId", "content", "fieldDesc"], "userId='{}'".format(userId))
        oldContent = None
        oldFieldDesc = None

        if len(listResult) <= 0:
            return

        for userInfo in listResult:
            oldContent = json.loads(userInfo["content"])
            oldFieldDesc = userInfo["fieldDesc"].split("#")

        if oldFieldDesc != newFieldDesc:
            # 取并集, 更新数据
            content = json.dumps(newContent | oldContent, ensure_ascii=False)
            listFieldDesc = list(set(newFieldDesc).union(set(oldFieldDesc)))
            listFieldDesc.sort()
            strField = [str(x) for x in listFieldDesc]
            fieldDesc = "#".join(strField)

            sql = "update 'UserInfo' set content='{}', fieldDesc='{}' where userId='{}'".format(content, fieldDesc, userId)
            if not self.db_.execute(sql):
                logger.warning("更新数据失败,{}", data)

    def getFieldDesc(self, data):
        listFieldDesc = []
        # 删除不存在的字段
        listDelKey = []
        for k, v in data.items():
            if k in self.dictField_:
                if v is not None:
                    if not (v.strip() == "" or v.strip() == "None"):
                        listFieldDesc.append(self.dictField_[k])
                else:
                    listDelKey.append(k)
        listFieldDesc.sort()

        for key in listDelKey:
            del data[key]

        return listFieldDesc

    # 插入一条数据
    def insertData(self, field, data, certainty = None):

        listFieldDesc = self.getFieldDesc(data)

        name = data[field]
        if certainty is None:
            id = ""
        else:
            id = data[certainty]
        content = json.dumps(data, ensure_ascii=False)
        strField = [str(x) for x in listFieldDesc]
        fieldDesc = "#".join(strField)

        sql = "insert into 'UserInfo'(userName, userId, content, fieldDesc) VALUES('{}', '{}', '{}', '{}')".format(name,
                                                                                                                   id,
                                                                                                                   content,
                                                                                                                   fieldDesc)
        if not self.db_.execute(sql):
            logger.warning("插入数据错误, {}", data)

    def searchCertaintyDataExists(self, field, certainty, data):
        tblName = "UserInfo"
        userId = data[certainty]
        if userId is None or userId == "" or userId == "None":
            return []
        return self.db_.select(tblName, ["userName"], "userId='{}'".format(userId))

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
                logger.info("属性替换:替换属性:{}, 替换为:{}", k, replaceValue)
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

        if data[field] == "None" or data[field] == "":
            # 数据无效
            logger.warning("无效的数据:{}", data)
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

        for field in listHeader:
            if field is None or field == "" or field == "None":
                continue

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
            self.dictField_[fieldName] = fieldId

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
