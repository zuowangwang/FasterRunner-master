# -*- coding: utf-8 -*-
import time
import json
import os
import io
import traceback
import string
import random
from copy import deepcopy
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, Template
from django.core.mail import EmailMultiAlternatives

from FasterRunner.settings import EMAIL_FROM, BASE_DIR, REPORTS_HOST
from fastrunner.utils.writeExcel import write_excel_log, get_error_response_content


def control_email(sample_summary, kwargs):
    if kwargs["strategy"] == '从不发送':
        return False
    elif kwargs["strategy"] == '始终发送':
        return True
    elif kwargs["strategy"] == '仅失败发送':
        for summary in sample_summary:
            if not summary["success"]:
                return True
    elif kwargs["strategy"] == '监控邮件':
        """
            新建一个monitor.json文件
            {
                task_name:{
                    "error_count": 0,
                    "error_message": ""
                }
            }
            runresultErrorMsg 是经过关键词过滤的执行结果，如果api调用失败后返回的报错信息内包含这些关键词，则将这个api的报错结果暂时记为空
            fail_count: 提前设置的错误此处阈值，超过则发送邮件

            1. 若 runresultErrorMsg == '' and error_message== '':  error_count = 0,error_message="" 不发送邮件
            2. 若 runresultErrorMsg == '' and error_message!= '':  error_count = 0,error_message="" 发送邮件
            3. 若 runresultErrorMsg != '' and error_message== '': error_count = 1, error_message=runresultErrorMsg，发送邮件
            4. 若 runresultErrorMsg != '' and error_message！= '' and error_message != runresultErrorMsg： error_count = 1,error_message=runresultErrorMsg 发送邮件
            5. 若 runresultErrorMsg！= '' and error_message != '' and error_message == runresultErrorMsg：
                3.1 若error_count <= fail_count: 发送邮件，error_count+1
                3.2 若error_count > fail_count: 不发送邮件，error_count+1
        """

        monitor_path = os.path.join(BASE_DIR, 'logs', 'monitor.json')
        if not os.path.isfile(monitor_path):
            all_json = {
                kwargs["task_name"]: {
                    "error_count": 0,
                    "error_message": ""
                }
            }
        else:
            with open(monitor_path, 'r', encoding='utf-8') as _json:
                all_json = json.load(_json)
            if kwargs["task_name"] not in all_json.keys():
                all_json[kwargs["task_name"]] = {
                        "error_count": 0,
                        "error_message": ""
                    }

        is_send_email = False
        last_json = all_json[kwargs["task_name"]]
        runresultErrorMsg = __filter_runresult(sample_summary, kwargs["self_error"])

        if runresultErrorMsg == '' and last_json["error_message"] == '':
            last_json["error_count"] = 0
            last_json["error_message"] = ""
            is_send_email = False
        elif runresultErrorMsg == '' and last_json["error_message"] != '':
            last_json["error_count"] = 0
            last_json["error_message"] = ""
            is_send_email = True
        elif runresultErrorMsg != '' and last_json["error_message"] == '':
            last_json["error_count"] = 1
            last_json["error_message"] = runresultErrorMsg
            is_send_email = True
        elif runresultErrorMsg != '' and last_json["error_message"] != '' and last_json["error_message"] != runresultErrorMsg:
            last_json["error_count"] = 1
            last_json["error_message"] = runresultErrorMsg
            is_send_email = True
        elif runresultErrorMsg != '' and last_json["error_message"] != '' and last_json["error_message"] == runresultErrorMsg:
            if last_json["error_count"] < int(kwargs["fail_count"]):
                is_send_email = True
            else:
                is_send_email = False
            last_json["error_count"] += 1

        all_json[kwargs["task_name"]] = last_json
        with open(monitor_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(all_json))

        return is_send_email

    else:
        return False


def send_result_email(send_subject, send_to, send_cc, send_text_content=None, send_html_content=None, send_file_path=[], from_email=EMAIL_FROM):
    """
    :param send_subject: str
    :param send_to: list
    :param send_cc: list
    :param send_text_content: str
    :param send_html_content: html
    :param from_email: str
    :param send_file_path: list
    :return: bool
    """
    try:
        msg = EmailMultiAlternatives(subject=send_subject, from_email=from_email, to=send_to, cc=send_cc)
        if send_text_content:
            msg.attach_alternative(send_text_content, 'text/plain')
        if send_html_content:
            msg.attach_alternative(send_html_content, 'text/html')
        if send_file_path:
            for file_path in send_file_path:
                msg.attach_file(file_path)
        send_status = msg.send()
        return send_status
    except Exception as e:
        print(traceback.print_exc())


def prepare_email_content(runresult, subject_name):
    """
    :param runresult: 生成的简要分析结果
    :param subject_name: html名称
    :return: email conetnt
    """
    batch_result = {}
    batch_result['report_name'] = subject_name
    batch_result["tasks"] = runresult["tasks"]
    batch_result["pass_task"] = runresult["pass_task"]
    batch_result["fail_task"] = runresult["fail_task"]
    batch_result['time_start'] = runresult["start_time"]
    batch_result['testsRun'] = runresult["testsRun"]
    batch_result['failures'] = runresult["failures"]
    batch_result['successes'] = runresult["successes"]
    batch_result['tests'] = runresult["tests"]
    batch_result['error_list'] = runresult["error_list"]

    report_template = Environment(loader=FileSystemLoader(BASE_DIR)).get_template('./templates/email_report.html')

    return report_template.render(batch_result)


def parser_runresult(sample_summary, sensitive_keys):
    tasks = 0
    pass_task = 0
    fail_task = 0
    testsRun = 0
    failures = 0
    successes = 0
    tests = []
    error_list = []
    for summary in sample_summary:
        # 删除指定的字段敏感信息,然后保存为html文件
        report_link = __generate_report(summary, sensitive_keys)
        test = {}
        test["status"] = 'success' if summary["success"] else 'error'
        test['name'] = summary["name"]
        test['link'] = '<a href=%s>%s</a>' % (report_link, test['name'])
        error_response_content = ''
        testsRun += len(summary["details"])
        for detail in summary["details"]:
            if not detail["success"]:
                failures += 1
                if int(detail["stat"]["failures"]) + int(detail["stat"]["errors"]) > 1:
                    for record in detail["records"]:
                        if record["status"] not in ["success", "skipped"]:
                            error_response = record["meta_data"]["response"]
                            if 'content' in error_response.keys() and error_response["content"] is not None:
                                error_response_content += error_response["content"] + '\n'
                            else:
                                error_response_content += record["attachment"] + '\n'
                else:
                    error_api = detail["records"][-1]
                    error_response = error_api["meta_data"]["response"]
                    if 'content' in error_response.keys() and error_response["content"] is not None:
                        error_response_content += error_response["content"] + '\n'
                    else:
                        error_response_content += error_api["attachment"] + '\n'

        if test["status"] == 'error':
            fail_task += 1
            err_msg = {}
            err_msg["proj"] = test['name']
            err_msg["content"] = error_response_content
            error_list.append(deepcopy(err_msg))

        tests.append(deepcopy(test))

    successes = testsRun - failures
    tasks = len(tests)
    pass_task = tasks - fail_task
    runresult = {
        "tasks": tasks,
        "pass_task": pass_task,
        "fail_task": fail_task,
        "testsRun": testsRun,
        "failures": failures,
        "successes": successes,
        "tests": tests,
        "error_list": error_list,
        "start_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sample_summary[0]["time"]["start_at"]))
    }
    return runresult


def prepare_email_file(summary_report):
    """
    :param summary_report: summary report
    :return: file path list
    """

    file_path = write_excel_log(summary_report)
    return [file_path]


def get_summary_report(sample_summary):
    # 汇总报告
    __summary = deepcopy(sample_summary)
    summary_report = __summary[0]
    for index, summary in enumerate(sample_summary):
        if index > 0:
            summary_report["success"] = summary["success"] if not summary["success"] else summary_report["success"]
            summary_report["stat"]["testsRun"] += summary["stat"]["testsRun"]
            summary_report["stat"]["failures"] += summary["stat"]["failures"]
            summary_report["stat"]["skipped"] += summary["stat"]["skipped"]
            summary_report["stat"]["successes"] += summary["stat"]["successes"]
            summary_report["stat"]["expectedFailures"] += summary["stat"]["expectedFailures"]
            summary_report["stat"]["unexpectedSuccesses"] += summary["stat"]["unexpectedSuccesses"]
            summary_report["time"]["duration"] += summary["time"]["duration"]
            summary_report["details"].extend(summary["details"])
    return summary_report


def __filter_runresult(sample_summary, self_error_list):
    runresultErrorMsg = ''
    for summary in sample_summary:
        runresult = get_error_response_content(summary["details"])[0]
        for testcase_result in runresult:
            for errormsg in testcase_result["error_api_content"]:
                if errormsg:
                    runresultErrorMsg += __is_self_error(errormsg[3].strip(), self_error_list)
    return runresultErrorMsg


def __is_self_error(error_content, self_error_list):
    if error_content and self_error_list:
        for error_message in self_error_list:
            if error_message in error_content:
                return ""
    return error_content


def del_sensitive_content(content, sensitive_keys):
    """ 通过邮件发送出去的都去除敏感信息,
        递归处理json，将敏感信息转换成****
    """
    SENSITIVE_CONTENT = '******'
    if isinstance(content, dict):
        for dict_key, dict_value in content.items():
            if dict_key in sensitive_keys:
                content[dict_key] = SENSITIVE_CONTENT
            else:
                content[dict_key] = del_sensitive_content(dict_value, sensitive_keys)
    elif isinstance(content, list):
        for index, i_content in enumerate(content):
            content[index] = del_sensitive_content(i_content, sensitive_keys)
    else:
        for key in sensitive_keys:
            if key in str(content):
                content = SENSITIVE_CONTENT
    return content


def __generate_report(summary, sensitive_keys):
    if isinstance(sensitive_keys, list) and sensitive_keys:
        for index, detail in enumerate(summary["details"]):
            summary["details"][index]["records"] = del_sensitive_content(detail["records"], sensitive_keys)
            summary["details"][index]["in_out"] = del_sensitive_content(detail["in_out"], sensitive_keys)

    start_at_timestamp = int(summary["time"]["start_at"])
    summary["time"]["start_datetime"] = datetime.fromtimestamp(start_at_timestamp).strftime('%Y-%m-%d %H:%M:%S')

    #  report_name = ''.join(random.choices(string.ascii_letters + string.digits, k=32))  # py3.5版本没有choices方法
    report_name = ''.join(random.sample(string.ascii_letters + string.digits, 32))
    relative_report_path = os.path.join('media', 'reports', "{}.html".format(report_name))
    report_template_path = os.path.join(BASE_DIR, 'templates', 'orgin_report_template.html')
    report_path = os.path.join(BASE_DIR, relative_report_path)
    if not os.path.isdir(os.path.dirname(report_path)):
        os.makedirs(os.path.dirname(report_path))
    with io.open(report_template_path, "r", encoding='utf-8') as fp_r:
        template_content = fp_r.read()
        with io.open(report_path, 'w', encoding='utf-8') as fp_w:
            rendered_content = Template(
                template_content,
                extensions=["jinja2.ext.loopcontrols"]
            ).render(summary)
            fp_w.write(rendered_content)
    report_link = os.path.join(REPORTS_HOST, relative_report_path)
    return report_link
