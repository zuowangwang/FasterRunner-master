
# _*_ coding:utf-8 _*_
import xlrd
import os

class Xlaccountinfo():
    # 获取excel数据，从第三行开始，第二行是表头，第一行是备注
    def __init__(self, path=''):
        self.xl = xlrd.open_workbook(path)

    def floattostr(self, val):
        if isinstance(val, float) and float(int(val)) != val:
            val = str(int(val))
        if val.lower() == 'true':
            val = True
        elif val.lower() == 'false':
            val = False
        return val

    def get_sheetinfo_by_name(self, name):
        self.sheet = self.xl.sheet_by_name(name)
        return self.get_sheet_info()

    def get_sheetinfo_by_index(self, index):
        self.sheet = self.xl.sheet_by_index(index)
        return self.get_sheet_info()

    def get_sheetinfo_by_rowName(self, name):
        self.sheet = self.xl.sheet_by_name(name)
        infolist = []
        for col in range(self.sheet.ncols):
            if col == 0:
                listKey = [self.floattostr(val.strip()) for val in self.sheet.col_values(col)]
            elif col == 1:
                info = [self.floattostr(val.strip()) for val in self.sheet.col_values(col)]
                tmp = zip(listKey, info)
                infolist.append(dict(tmp))
        return infolist

    def get_sheet_info(self):
        infolist = []
        for row in range(1, self.sheet.nrows):
            if row == 1:
                listKey = [self.floattostr(val.strip()) for val in self.sheet.row_values(row)]
            else:
                info = [self.floattostr(val.strip()) for val in self.sheet.row_values(row)]
                tmp = zip(listKey, info)
                infolist.append(dict(tmp))
        return infolist


# 通过行获取excel数据
def get_xlsx_by_cols(excelName, sheetName):
    xlinfo = Xlaccountinfo(excelName)
    info = xlinfo.get_sheetinfo_by_name(sheetName)
    return info

# 通过列获取excel数据
def xlsxPlatform(excelName, sheetName):
    xlinfo = Xlaccountinfo(excelName)
    info = xlinfo.get_sheetinfo_by_rowName(sheetName)
    return info
    
if __name__ == '__main__':
    excelName = os.environ["excelName"]
    sheetName = os.environ["excelsheet"]
                                     