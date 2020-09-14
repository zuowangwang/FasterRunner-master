#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json
import logging
import traceback

from rest_framework.response import Response

from fastrunner import models


def get_value(content, keys):
    if isinstance(content, (str, int)):
        return content
    if content == None:
        return ""
    if isinstance(content, (list, dict)):
        for k in keys:
            keys.remove(k)
            try:
                data = content[int(k)]
            except:
                data = content.get(k, "")
            finally:
                return get_value(data, keys)


def get_para(val, text):
    """get para.

    """
    content = json.loads(text)
    keys = val.split(".")[1:]
    value = get_value(content, keys)
    return value


def add_global_variable(extracts, id, content):
    project = models.Project.objects.get(id=id)
    for ext in extracts:
        try:
            for k, v in ext.items():
                val = get_para(v, content)
                _, tag = models.Variables.objects.update_or_create(project=project, key=k,
                                                                   defaults={"value": val})
        except Exception as e:
            traceback.print_exc()
            logging.error("添加参数为全局变量失败： {}".format(str(ext)))
            return Response({"traceback": str(e)}, "400")