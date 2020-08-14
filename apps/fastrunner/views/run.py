import json
import logging

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from djcelery import models as celery_models

from fastrunner import tasks
from fastrunner.utils.decorator import request_log
from fastrunner.utils.host import parse_host
from fastrunner.utils.parser import Format
from fastrunner.utils import loader
from fastrunner.utils.permissions import IsBelongToProject
from fastrunner import models

"""运行方式
"""
logger = logging.getLogger('FasterRunner')

config_err = {
    "success": False,
    "msg": "指定的配置文件不存在",
    "code": "9999"
}


@api_view(['POST'])
@request_log(level='INFO')
def run_api(request):
    """ run api by body
    """
    name = request.data.pop('config')
    host = request.data.pop("host")
    api = Format(request.data)
    api.parse()

    config = None
    if name != '请选择':
        try:
            config = eval(models.Config.objects.get(name=name, project__id=api.project).body)
        except ObjectDoesNotExist:
            logger.error("指定配置文件不存在:{name}".format(name=name))
            return Response(config_err)

    temp_config = []
    temp_baseurl = ''
    if host != "请选择":
        host = models.HostIP.objects.get(name=host, project=api.project)
        host_info = json.loads(host.hostInfo)
        temp_config.extend(host_info["variables"])
        temp_baseurl = host.base_url if host.base_url else ''

    if config and host != "请选择":
        config["variables"].extend(temp_config)
        if temp_baseurl:
            config["request"]["base_url"] = temp_baseurl
    if not config and host != "请选择":
        config = {
            "variables": temp_config,
            "request": {
                "base_url": temp_baseurl
            }
        }

    # if host != "请选择":
    #     try:
    #         host = models.HostIP.objects.get(name=host, project__id=api.project).value.splitlines()
    #         api.testcase = parse_host(host, api.testcase)
    #     except ObjectDoesNotExist:
    #         logger.error("指定域名不存在:{name}".format(name=host))
    try:
        summary = loader.debug_api(api.testcase, api.project, config=parse_host(host, config))
    except Exception as e:
        return Response({'traceback': str(e)}, status=400)
    return Response(summary)


@api_view(['GET'])
@request_log(level='INFO')
def run_api_pk(request, **kwargs):
    """run api by pk and config
    """
    host = request.query_params["host"]
    api = models.API.objects.get(id=kwargs['pk'])
    name = request.query_params["config"]
    config = None if name == '请选择' else eval(models.Config.objects.get(name=name, project=api.project).body)
    test_case = eval(api.body)

    temp_config = []
    temp_baseurl = ''
    if host != "请选择":
        host = models.HostIP.objects.get(name=host, project=api.project)
        host_info = json.loads(host.hostInfo)
        temp_config.extend(host_info["variables"])
        temp_baseurl = host.base_url if host.base_url else ''

    if config and host != "请选择":
        config["variables"].extend(temp_config)
        if temp_baseurl:
            config["request"]["base_url"] = temp_baseurl
    if not config and host != "请选择":
        config = {
            "variables": temp_config,
            "request": {
                "base_url": temp_baseurl
            }
        }
    # if host != "请选择":
    #     try:
    #         host = models.HostIP.objects.get(name=host, project=api.project).value.splitlines()
    #         test_case = parse_host(host, test_case)
    #     except ObjectDoesNotExist:
    #         logger.error("指定域名不存在:{name}".format(name=host))
    try:
        summary = loader.debug_api(test_case, api.project.id, config=parse_host(host, config))
    except Exception as e:
        return Response({'traceback': str(e)}, status=400)

    return Response(summary)


@api_view(['POST'])
@request_log(level='INFO')
def run_api_tree(request):
    """run api by tree
    {
        project: int
        relation: list
        name: str
        async: bool
        host: str
    }
    """
    # order by id default
    host = request.data["host"]
    project = request.data['project']
    relation = request.data["relation"]
    back_async = request.data["async"]
    name = request.data["name"]
    config = request.data["config"]

    config = None if config == '请选择' else eval(models.Config.objects.get(name=config, project__id=project).body)
    test_case = []

    temp_config = []
    temp_baseurl = ''
    if host != "请选择":
        host = models.HostIP.objects.get(name=host, project=project)
        host_info = json.loads(host.hostInfo)
        temp_config.extend(host_info["variables"])
        temp_baseurl = host.base_url if host.base_url else ''

    if config and host != "请选择":
        config["variables"].extend(temp_config)
        if temp_baseurl:
            config["request"]["base_url"] = temp_baseurl
    if not config and host != "请选择":
        config = {
            "variables": temp_config,
            "request": {
                "base_url": temp_baseurl
            }
        }

    for relation_id in relation:
        api = models.API.objects.filter(project__id=project, relation=relation_id).order_by('id').values('body')
        for content in api:
            api = eval(content['body'])
            test_case.append(parse_host(host, api))

    if back_async:
        tasks.async_debug_api.delay(test_case, project, name, config=parse_host(host, config))
        summary = loader.TEST_NOT_EXISTS
        summary["msg"] = "接口运行中，请稍后查看报告"
    else:
        try:
            summary = loader.debug_api(test_case, project, config=parse_host(host, config))
        except Exception as e:
            return Response({'traceback': str(e)}, status=400)

    return Response(summary)


@api_view(["POST"])
@request_log(level='INFO')
def run_testsuite_pk(request, **kwargs):
    """run testsuite by pk
        {
            project: int,
            name: str,
            host: str,
            testDataExcel: str
            testDataSheet: str
        }
    """
    pk = kwargs["pk"]
    test_list = models.CaseStep.objects.filter(case__id=pk).order_by("step").values("body")

    project = request.data["project"]
    name = request.data["name"]
    host = request.data["host"]
    back_async = request.data["async"]
    report_name = request.data["reportName"]

    test_data = None
    if request.data["excelTreeData"]:
        test_data = tuple(request.data["excelTreeData"])

    test_case = []
    config = None

    temp_config = []
    temp_baseurl = ''
    if host != "请选择":
        host = models.HostIP.objects.get(name=host, project=project)
        host_info = json.loads(host.hostInfo)
        temp_config.extend(host_info["variables"])
        temp_baseurl = host.base_url if host.base_url else ''

    for content in test_list:
        body = eval(content["body"])

        if "base_url" in body["request"].keys():
            config = eval(models.Config.objects.get(name=body["name"], project__id=project).body)
            continue

        test_case.append(parse_host(host, body))

    if config and host != "请选择":
        config["variables"].extend(temp_config)
        if temp_baseurl:
            config["request"]["base_url"] = temp_baseurl
    if not config and host != "请选择":
        config = {
            "variables": temp_config,
            "request": {
                "base_url": temp_baseurl
            }
        }

    try:
        if back_async:
            tasks.async_debug_test.delay(test_case, project, name=name, report_name=report_name, config=parse_host(host, config), test_data=test_data)
            summary = loader.TEST_NOT_EXISTS
            summary["msg"] = "用例运行中，请稍后查看报告"
        else:
            summary = loader.debug_api(test_case, project, name=name, config=parse_host(host, config), save=True, test_data=test_data, report_name=report_name)
        return Response(summary)
    except Exception as e:
        return Response({'traceback': str(e)}, status=400)


@api_view(['GET'])
@request_log(level='INFO')
def run_schedule_test(request, **kwargs):
    try:
        pk = kwargs["pk"]
        test_case = celery_models.PeriodicTask.objects.get(id=pk)
        run_args = json.loads(test_case.args)
        run_kwargs = json.loads(test_case.kwargs)
        run_kwargs["strategy"] = '始终发送'
        tasks.schedule_debug_suite.delay(*run_args, **run_kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({'traceback': str(e)}, status=400)


@api_view(['POST'])
@request_log(level='INFO')
def run_suite_tree(request):
    """run suite by tree
    {
        project: int
        relation: list
        name: str
        async: bool
        host: str
    }
    """
    # order by id default
    try:
        project = request.data['project']
        relation = request.data["relation"]
        report_name = request.data["name"]
        host = request.data["host"]

        temp_config = []
        temp_baseurl = ''
        if host != "请选择":
            host = models.HostIP.objects.get(name=host, project=project)
            host_info = json.loads(host.hostInfo)
            temp_config.extend(host_info["variables"])
            temp_baseurl = host.base_url if host.base_url else ''

        test_sets = []
        suite_list = []
        config_list = []
        for relation_id in relation:
            suite = list(models.Case.objects.filter(project__id=project,
                                                    relation=relation_id).order_by('id').values('id', 'name'))
            for content in suite:
                test_list = models.CaseStep.objects.filter(case__id=content["id"]).order_by("step").values("body")

                testcase_list = []
                config = None
                for case_content in test_list:
                    body = eval(case_content["body"])
                    if "base_url" in body["request"].keys():
                        config = eval(models.Config.objects.get(name=body["name"], project__id=project).body)
                        continue
                    testcase_list.append(parse_host(host, body))
                # [[{scripts}, {scripts}], [{scripts}, {scripts}]]
                if config and host != "请选择":
                    config["variables"].extend(temp_config)
                    if temp_baseurl:
                        config["request"]["base_url"] = temp_baseurl
                if not config and host != "请选择":
                    config = {
                        "variables": temp_config,
                        "request": {
                            "base_url": temp_baseurl
                        }
                    }
                config_list.append(parse_host(host, config))
                test_sets.append(testcase_list)
                suite_list = suite_list + suite

        tasks.async_debug_suite.delay(test_sets, project, suite_list, report_name, config_list)
        summary = loader.TEST_NOT_EXISTS
        summary["msg"] = "用例运行中，请稍后查看报告"

        return Response(summary)
    except Exception as e:
        return Response({'traceback': str(e)}, status=400)
