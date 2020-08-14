# _*_ coding: utf-8 _*_
import json
from fastrunner import models
from fastrunner.utils.parser import Format
from djcelery import models as celery_models


def get_counter(model, pk=None):
    """
    统计相关表长度
    """
    if pk:
        return model.objects.filter(project__id=pk).count()
    else:
        return model.objects.count()


def get_project_detail(pk):
    """
    项目详细统计信息
    """
    api_count = get_counter(models.API, pk=pk)
    case_count = get_counter(models.Case, pk=pk)
    config_count = get_counter(models.Config, pk=pk)
    variables_count = get_counter(models.Variables, pk=pk)
    report_count = get_counter(models.Report, pk=pk)
    host_count = get_counter(models.HostIP, pk=pk)
    task_count = celery_models.PeriodicTask.objects.filter(description=pk).count()

    return {
        "api_count": api_count,
        "case_count": case_count,
        "task_count": task_count,
        "config_count": config_count,
        "variables_count": variables_count,
        "report_count": report_count,
        "host_count":host_count
    }


def tree_end(params, project):
    """
    project: Project Model
    params: {
        node: int,
        type: int
    }
    """
    type = params['type']
    node = params['node']

    if type == 1:
        models.API.objects.filter(relation=node, project=project).delete()

    # remove node testcase
    elif type == 2:
        case = models.Case.objects.filter(relation=node, project=project).values('id')

        for case_id in case:
            models.CaseStep.objects.filter(case__id=case_id['id']).delete()
            models.Case.objects.filter(id=case_id['id']).delete()


def update_casestep(body, case):
    step_list = list(models.CaseStep.objects.filter(case=case).values('id'))

    for index in range(len(body)):
        test = body[index]
        if 'newBody' in test.keys():
            format_http = Format(test['newBody'])
            format_http.parse()
            name = format_http.name
            new_body = format_http.testcase
            if 'case' in test.keys():
                case_step = models.CaseStep.objects.get(id=test['id'])
                api_id = case_step.apiId
            else:
                api_id = test['id']
            api = models.API.objects.get(id=api_id)
            url = api.url
            method = api.method
            api_body = eval(api.body)
            new_body["request"] = api_body["request"]
            new_body["desc"]["header"] = api_body["desc"]["header"]
            new_body["desc"]["data"] = api_body["desc"]["data"]
            new_body["desc"]["files"] = api_body["desc"]["files"]
            new_body["desc"]["params"] = api_body["desc"]["params"]

        else:
            if 'case' in test.keys():
                case_step = models.CaseStep.objects.get(id=test['id'])
                new_body = eval(case_step.body)
                if case_step.method != "config":
                    api_id = case_step.apiId
                    api = models.API.objects.get(id=api_id)
                    api_body = eval(api.body)
                    url = api.url
                    method = api.method
                    new_body["request"] = api_body["request"]
                    new_body["desc"]["header"] = api_body["desc"]["header"]
                    new_body["desc"]["data"] = api_body["desc"]["data"]
                    new_body["desc"]["files"] = api_body["desc"]["files"]
                    new_body["desc"]["params"] = api_body["desc"]["params"]
                else:
                    url = ""
                    method = "config"
                    api_id = 0
            elif test["body"]["method"] == "config":
                case_step = models.Config.objects.get(name=test['body']['name'])
                new_body = eval(case_step.body)
                url = ""
                method = "config"
                api_id = 0
            else:
                case_step = models.API.objects.get(id=test['id'])
                new_body = eval(case_step.body)
                url = case_step.url
                method = case_step.method
                api_id = case_step.id

            name = test['body']['name']
            new_body['name'] = name

        kwargs = {
            "name": name,
            "body": new_body,
            "url": url,
            "method": method,
            "step": index,
            "apiId": api_id
        }
        if 'case' in test.keys():
            models.CaseStep.objects.filter(id=test['id']).update(**kwargs)
            step_list.remove({"id": test['id']})
        else:
            kwargs['case'] = case
            models.CaseStep.objects.create(**kwargs)

    #  去掉多余的step
    for content in step_list:
        models.CaseStep.objects.filter(id=content['id']).delete()


def generate_casestep(body, case):
    """
    生成用例集步骤
    [{
        id: int,
        project: int,
        name: str
    }]

    """
    #  index也是case step的执行顺序

    for index in range(len(body)):

        test = body[index]
        try:
            format_http = Format(test['newBody'])
            format_http.parse()
            name = format_http.name
            new_body = format_http.testcase

            apiId = test['id']
            api = models.API.objects.get(id=apiId)
            url = api.url
            method = api.method
            new_body['name'] = name
            api_body = eval(api.body)
            new_body["request"] = api_body["request"]
            new_body["desc"]["header"] = api_body["desc"]["header"]
            new_body["desc"]["data"] = api_body["desc"]["data"]
            new_body["desc"]["files"] = api_body["desc"]["files"]
            new_body["desc"]["params"] = api_body["desc"]["params"]

        except KeyError:
            if test["body"]["method"] == "config":
                name = test["body"]["name"]
                method = test["body"]["method"]
                config = models.Config.objects.get(name=name, project=case.project)
                url = config.base_url
                new_body = eval(config.body)
                apiId = 0
            else:
                apiId = test['id']
                api = models.API.objects.get(id=apiId)
                url = api.url
                method = api.method
                new_body = eval(api.body)
                name = test['body']['name']
                new_body['name'] = name

        kwargs = {
            "name": name,
            "body": new_body,
            "url": url,
            "method": method,
            "step": index,
            "case": case,
            "apiId": apiId
        }

        models.CaseStep.objects.create(**kwargs)


def case_end(pk, project_id):
    """
    pk: int case id
    """
    # 删除定时任务里的case
    tasks = celery_models.PeriodicTask.objects.filter(description=project_id)
    for task in tasks:
        task_args = json.loads(task.args)
        for index in range(len(task_args)):
            if task_args[index]["id"] == pk:
                del task_args[index]
        task.args = json.dumps(task_args)
        task.save()
    models.CaseStep.objects.filter(case__id=pk).delete()
    models.Case.objects.filter(id=pk).delete()


def api_end(pk):
    models.CaseStep.objects.filter(apiId=pk).delete()
    models.API.objects.get(id=pk).delete()
