# _*_ coding:utf-8 _*_
import os
from get_excel_data import xlsxPlatform,get_xlsx_by_cols

def get_excel_info():
        group = os.environ["excelName"] 
        insurance = os.environ["excelsheet"]
        tempInfo = xlsxPlatform(group, insurance)
        return tempInfo
        
def get_excel_info_clos():
        group = os.environ["excelName"] 
        insurance = os.environ["excelsheet"]
        tempInfo = get_xlsx_by_cols(group, insurance)
        return tempInfo

def cc1():
    cc = '123999999'
    return cc
    
def up_data(request):
    import json
    request["json"] = json.dumps(request["json"]).replace(" ",'')