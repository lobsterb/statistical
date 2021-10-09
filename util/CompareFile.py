# coding:utf-8
import hashlib
from loguru import logger
from util.xlsxreader import XlsxReader


class CompareFile:

    class SheetInfo:
        def __init__(self, sheetName, sheetHeader, sheetData):
            self.sheetName_ = sheetName
            self.sheetHeader_ = sheetHeader
            self.sheetData_ = sheetData

    def __init__(self, filePath, checkHandleFile):
        self.filePath_ = filePath
        self.md5_ = self.getFileMd5()
        logger.info("开始处理文件:{},MD5:{}", self.filePath_, self.md5_)
        self.isHandle_ = checkHandleFile(self.filePath_, self.md5_)
        if not self.isHandle_:
            self.reader_ = XlsxReader(filePath)
            self.sheets_ = self.readAllData()

    # 获取文件md5
    def getFileMd5(self):
        m = hashlib.md5()
        with open(self.filePath_, "rb") as f:
            while True:
                data = f.read(4096)
                if not data:
                    break
                m.update(data)
        return m.hexdigest()

    # 读取全部数据
    def readAllData(self):
        listData = []
        sheetNames = self.reader_.sheetNames_
        for sheet in sheetNames:
            logger.info("读取sheet:{}", sheet)
            self.reader_.openSheet(sheet)
            sheetHeader = self.reader_.openSheetHeader_
            sheetData = self.reader_.readAllData()
            self.reader_.closeSheet()
            sheetInfo = CompareFile.SheetInfo(sheet, sheetHeader, sheetData)
            listData.append(sheetInfo)
            logger.info("读取信息数量:{}", len(sheetData))
        return listData


