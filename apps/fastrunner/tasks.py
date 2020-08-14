# _*_ coding: utf-8 _*_
import django
django.setup()

import json

from celery import shared_task  # 可以无需任何具体的应用程序实例创建任务

from fastrunner import models
from fastrunner.utils.loader import save_summary, debug_suite, debug_api
from fastrunner.utils.host import parse_host
from fastrunner.utils.email_send import send_result_email, prepare_email_content, control_email, parser_runresult, prepare_email_file, get_summary_report


@shared_task
def async_debug_api(api, project, name, config=None):
    """异步执行api
    """
    summary = debug_api(api, project, config=config, save=False)
    save_summary(name, summary, project)


@shared_task
def async_debug_test(test_case, project, name, report_name, config, test_data):
    """异步执行testcase
    """
    summary = debug_api(test_case, project, name=name, config=config, save=False, test_data=test_data)
    save_summary(report_name, summary, project)


@shared_task
def async_debug_suite(suite, project, obj, report, config):
    """异步执行suite
    """
    summary = debug_suite(suite, project, obj, config=config, save=False)
    save_summary(report, summary, project)


@shared_task
def schedule_debug_suite(*args, **kwargs):
    """定时任务
    """
    project = int(kwargs["project"])

    sample_summary = []
    if not args:
        raise ValueError('任务列表为空，请检查')
    for cases in args:
        case_kwargs = cases.get('kwargs', '')
        test_list = models.CaseStep.objects.filter(case__id=cases["id"]).order_by("step").values("body")
        if not test_list:
            raise ValueError('用例缺失，请假查')
        report_name = cases["name"]
        case_name = cases["name"]
        test_case = []
        config = None
        temp_config = []
        test_data = None
        temp_baseurl = ''
        g_host_info = ''
        if case_kwargs:
            report_name = case_kwargs["testCaseName"]
            if case_kwargs.get("excelTreeData", []):
                test_data = tuple(case_kwargs["excelTreeData"])
            if case_kwargs["hostInfo"] and case_kwargs["hostInfo"] != "请选择":
                g_host_info = case_kwargs["hostInfo"]
                host = models.HostIP.objects.get(name=g_host_info, project__id=project)
                _host_info = json.loads(host.hostInfo)
                temp_config.extend(_host_info["variables"])
                temp_baseurl = host.base_url if host.base_url else ''

        for content in test_list:
            body = eval(content["body"])
            if "base_url" in body["request"].keys():
                config = eval(models.Config.objects.get(name=body["name"], project__id=project).body)
                continue
            test_case.append(parse_host(g_host_info, body))

        if config and g_host_info not in ["请选择", '']:
            config["variables"].extend(temp_config)
            if temp_baseurl:
                config["request"]["base_url"] = temp_baseurl
        if not config and g_host_info not in ["请选择", '']:
            config = {
                "variables": temp_config,
                "request": {
                    "base_url": temp_baseurl
                }
            }

        summary = debug_api(test_case, project, name=case_name, config=parse_host(g_host_info, config), save=False, test_data=test_data)
        summary["name"] = report_name
        sample_summary.append(summary)

    if sample_summary:
        summary_report = get_summary_report(sample_summary)
        save_summary(kwargs["task_name"], summary_report, project, type=3)
        is_send_email = control_email(sample_summary, kwargs)
        if is_send_email:
            sensitive_keys = kwargs.get('sensitive_keys', [])
            runresult = parser_runresult(sample_summary, sensitive_keys)

            peoject_name = models.Project.objects.get(id=project).name
            subject_name = peoject_name + ' - ' + kwargs["task_name"]
            if runresult["fail_task"] > 0:
                subject_name += " - 失败：" + ",".join([err_msg["proj"] for err_msg in runresult["error_list"]])
            else:
                subject_name += " - 成功！"
            html_conetnt = prepare_email_content(runresult, subject_name)
            send_file_path = prepare_email_file(summary_report)
            send_status = send_result_email(subject_name, kwargs["receiver"], kwargs["mail_cc"], send_html_content=html_conetnt, send_file_path=send_file_path)
            if send_status:
                print('邮件发送成功')
            else:
                print('邮件发送失败')
