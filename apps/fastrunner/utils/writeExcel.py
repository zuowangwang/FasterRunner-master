import os
import xlsxwriter
import time

from FasterRunner.settings import MEDIA_ROOT


class WriteExcel(object):
    """写excel
    """
    def __init__(self, path):
        self.row = 0
        self.xl = xlsxwriter.Workbook(path)
        self.style = self.xl.add_format({'bg_color': 'green'})

    def xl_write(self, *args):
        col = 0
        style = ''
        if 'pass' in args:
            style = self.style
        for val in args:
            if isinstance(val, list):
                for value in val:
                    self.sheet.write_string(self.row, col, value, style)
                    col += 1
            else:
                self.sheet.write_string(self.row, col, val, style)
                col += 1
        self.row += 1

    def log_init(self, sheetname, *title):
        self.sheet = self.xl.add_worksheet(sheetname)
        self.sheet.set_column('A:A', 20)  # 测试报告名称
        self.sheet.set_column('B:B', 10)  # 用例状态
        self.sheet.set_column('C:C', 25)  # 报错接口
        self.xl_write(*title)

    def log_write(self, *args):
        self.xl_write(*args)

    def xl_close(self):
        self.xl.close()


def write_excel_log(summary):
    """
    将json报告整理为简易的excel报告并存到media目录下
    """
    basepath = os.path.join(MEDIA_ROOT, 'excelReport')
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    reporttime = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(summary["time"]["start_at"]))
    reportname = reporttime + '.xlsx'
    excel_report_path = os.path.join(basepath, reportname)
    if not os.path.exists(excel_report_path):
        error_content, out_keys = get_error_response_content(summary["details"])

        # 初始化excel表格表头
        error_api_count = 0
        for testcase_result in error_content:
            if len(testcase_result["error_api_content"]) > error_api_count:
                error_api_count = len(testcase_result["error_api_content"])
        error_api_keys = []
        error_api_keys_one = []
        if error_api_count:
            for index in range(error_api_count):
                error_api_keys.extend(['报错接口 - '+str(index+1), 'traceback', '请求报文', '返回报文'])
                error_api_keys_one.extend(['error_api'+str(index+1), 'traceback', 'request', 'response'])

        xinfo = WriteExcel(excel_report_path)
        xinfo.log_init('cases', '测试用例名称', '用例状态', out_keys, error_api_keys)
        xinfo.log_write('name', 'status', out_keys, error_api_keys_one)
        for testcase_result in error_content:
            error_api_content = []
            for _ in testcase_result["error_api_content"]:
                error_api_content.extend(_)
            xinfo.log_write(testcase_result["case_name"], testcase_result["testcase_status"], testcase_result["out_values"], error_api_content)
        xinfo.xl_close()

    return excel_report_path


def get_error_response_content(summary_details):
    """
    将json报告中的报错信息罗列出来
    :param summary_details: list summary["details"]
    :return: content:[{
                testcase_status: 'pass'/'fail'
                error_api_content: list , [['','','',''],[]]列表内固定4个值 ["error_api_name","error_traceback","error_request_body","error_response_content"]
                out_values: list
            },{...}]
            out_keys: list
    """
    content = []

    temp_out_keys = []
    for testcases in summary_details:
        temp_out_keys.extend(testcases["in_out"]["out"].keys())
    out_keys = list(set(temp_out_keys))
    # 遍历用例个数
    for testcases in summary_details:
        testcase_result = {
            "case_name": testcases["name"],
            "testcase_status": 'pass',
            "error_api_content": [],
            "out_values": []
        }
        if not testcases["success"]:
            # 遍历用例的api，如果错误数量大于一，则全部遍历，小于等于1则直接取最后一个api
            if int(testcases["stat"]["failures"]) + int(testcases["stat"]["errors"]) > 1:
                for record in testcases["records"]:
                    if record["status"] not in ["success", "skipped"]:
                        error_request = record["meta_data"]["request"]
                        error_response = record["meta_data"]["response"]
                        error_api_name = record["name"]
                        error_traceback = record["attachment"]
                        error_request_body = error_request["body"] \
                            if 'body' in error_request.keys() and error_request["body"] is not None else ''
                        error_response_content = error_response["content"] \
                            if 'content' in error_response.keys() and error_response["content"] is not None else ''
                        testcase_result["error_api_content"].append([error_api_name, error_traceback, error_request_body, error_response_content])
            else:
                error_api = testcases["records"][-1]
                error_request = error_api["meta_data"]["request"]
                error_response = error_api["meta_data"]["response"]
                error_api_name = error_api["name"]
                error_traceback = error_api["attachment"]
                error_request_body = error_request["body"] \
                    if 'body' in error_request.keys() and error_request["body"] is not None else ''
                error_response_content = error_response["content"] \
                    if 'content' in error_response.keys() and error_response["content"] is not None else ''
                testcase_result["error_api_content"].append([error_api_name, error_traceback, error_request_body, error_response_content])
            testcase_result["testcase_status"] = 'fail'

        testcase_result["out_values"] = [''] * len(out_keys)
        for out_key, out_value in testcases["in_out"]["out"].items():
            if out_key in out_keys:
                testcase_result["out_values"][out_keys.index(out_key)] = str(out_value)
        content.append(testcase_result)
    return content, out_keys
