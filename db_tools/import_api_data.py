# -*- coding: utf-8 -*-
__author__ = 'xukexin'

import os
import sys
import yaml
import io
import json
import traceback


sys.path.append("./")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FasterRunner.settings")

import django
django.setup()

from fastrunner.utils.parser import Format
from fastrunner import models


def load_yaml_file(yaml_file):
    """ load yaml file and check file content format
    """
    with io.open(yaml_file, 'r', encoding='utf-8') as stream:
        try:
            yaml_content = yaml.load(stream)
        except:
            raise ValueError(traceback.print_exc())

        return yaml_content


def load_json_file(json_file):
    """ load json file and check file content format
    """
    with io.open(json_file, encoding='utf-8') as data_file:
        try:
            json_content = json.load(data_file)
        except:
            raise ValueError(traceback.print_exc())
        return json_content


def get_tree_max_id(value, list_id=[]):
    """
    得到最大Tree max id
    """
    if not value:
        return 0  # the first node id

    if isinstance(value, list):
        for content in value:  # content -> dict
            try:
                children = content['children']
            except KeyError:
                """
                待返回错误信息
                """
                pass
            if children:
                get_tree_max_id(children)

            list_id.append(content['id'])

    return max(list_id)


def get_desc(content):
    desc_dict = {}
    if isinstance(content, dict):
        for key in content.keys():
            desc_dict[key] = ""
    elif isinstance(content, list):
        for key_value in content:
            for key in key_value.keys():
                desc_dict[key] = ""
    if desc_dict:
        return desc_dict
    else:
        raise ValueError("get desc miss")


def paeser_api(content):
    """"生成前端的标准格式
        暂未对file做处理
    """
    request_data = {
        "header": {
            "header": {},
            "desc": {}
        },
        "request": {
            "form": {
                "data": {},
                "desc": {}
            },
            "json": {},
            "params": {
                "params": {},
                "desc": {}
            },
            "files": {
                "files": {},
                "desc": {}
            }
        },
        "extract": {
            "extract": [],
            "desc": {}
        },
        "validate": {
            "validate": []
        },
        "variables": {
            "variables": [],
            "desc": {}
        },
        "hooks": {
            "setup_hooks": [],
            "teardown_hooks": []
        },
        "url": "",
        "method": "",
        "name": "",
        "times": 1
    }
    if isinstance(content, dict):
        """ v2 httprunner """

    elif isinstance(content, list):
        """httprunner v1 只取第一个接口"""
        content = content[0]["api"]
    else:
        return ''

    for key, value in content.items():
        if key == 'name':
            request_data["name"] = value
        if key == 'def':
            request_data["name"] = value.split('(')[0]
        if key == 'request':
            for req_key, req_value in value.items():
                if req_key == 'data':
                    if isinstance(req_value, str):
                        data = req_value.split('&')
                        if '=' in data:
                            for key_value in data:
                                temp = key_value.split('=')
                                data_key = temp[0]
                                data_value = temp[1]
                                request_data["request"]["form"]["data"][data_key] = data_value
                            request_data["request"]["form"]["desc"] = get_desc(request_data["request"]["form"]["data"])
                        else:
                            request_data["request"]["form"]["data"] = {req_value: ""}
                            request_data["request"]["form"]["desc"] = {req_value: ""}
                    elif isinstance(req_value, dict):
                        request_data["request"]["form"]["data"] = req_value
                        request_data["request"]["form"]["desc"] = get_desc(req_value)
                if req_key == 'headers':
                    request_data["header"]["header"] = req_value
                    request_data["header"]["desc"] = get_desc(req_value)
                if req_key == 'json':
                    request_data["request"]["json"] = req_value
                if req_key == 'params':
                    request_data["request"]["params"]["params"] = req_value
                    request_data["request"]["params"]["desc"] = get_desc(req_value)
                if req_key == 'method':
                    request_data["method"] = req_value
                if req_key == 'url':
                    request_data["url"] = req_value
        if key == 'extract' and value:
            request_data["extract"]["extract"] = value
            request_data["extract"]["desc"] = get_desc(value)
        if key == 'validate':
            request_data["validate"]["validate"] = value
        if key == 'variables':
            if isinstance(value, list):
                request_data["variables"]["variables"] = value
            if isinstance(value, dict):
                for var_key, var_value in value.items():
                    request_data["variables"]["variables"].append({var_key: var_value})
            request_data["variables"]["desc"] = get_desc(value)
        if key == 'setup_hooks':
            request_data["hooks"]["setup_hooks"] = value
        if key == 'teardown_hooks':
            request_data["hooks"]["teardown_hooks"] = value
        if key == 'times':
            request_data["times"] = value
    return request_data


def save_api(request_data, now_tree):
    if request_data:
        api = Format(request_data)
        api.parse()
        api_body = {
            'name': api.name,
            'body': api.testcase,
            'url': api.url,
            'method': api.method,
            'project_id': PROJECT_ID,
            'relation': now_tree["id"]
        }
        print(api_body)
        try:
            models.API.objects.create(**api_body)
        except:
            print(traceback.print_exc())


# 递归处理
def import_api_data(file_path, now_tree):
    """
    file_path: import api dir path
    global_id: now api_tree max_id
    dowhat:
        make {
            "id":max_id,
            'lable': 'api',
            'children': [
                {
                "id":max_id++,
                'lable': 'dir_name',
                children: []
                }
            ]
        }
    """

    path_dir = os.listdir(file_path)
    for file_name in path_dir:
        now_dir_path = os.path.join(file_path, file_name)
        if os.path.isfile(now_dir_path):
            file_suffix = os.path.splitext(now_dir_path)[1].lower()
            if file_suffix == '.json':
                file_content = load_json_file(now_dir_path)
                request_data = paeser_api(file_content)
                save_api(request_data, now_tree)
            elif file_suffix in ['.yaml', '.yml']:
                file_content = load_yaml_file(now_dir_path)
                request_data = paeser_api(file_content)
                save_api(request_data, now_tree)

        elif os.path.isdir(now_dir_path):
            global max_tree_id
            max_tree_id += 1
            next_tree = {
                "label": os.path.basename(now_dir_path),
                "id": max_tree_id + 1,
                "children": []
            }
            now_tree["children"].append(next_tree)
            import_api_data(now_dir_path, next_tree)
            global new_tree
            new_tree.append(now_tree)


if __name__ == '__main__':
    MY_API_FILEPATH = r'D:\haibotest\api-tests\noDealer\api'
    PROJECT_ID = 6  # 看自己现在的项目id

    TREE_TYPE = 1
    relation = models.Relation.objects.get(project__id=PROJECT_ID, type=TREE_TYPE)
    tree = eval(relation.tree)
    max_tree_id = get_tree_max_id(tree)
    now_tree = {
        "label": os.path.basename(MY_API_FILEPATH),
        "id": max_tree_id + 1,
        "children": []
    }
    new_tree = []
    import_api_data(MY_API_FILEPATH, now_tree)
    tree.append(new_tree[-1])
    relation.tree = tree
    print(relation.tree)

    relation.save()
