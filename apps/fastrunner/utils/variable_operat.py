#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json
import logging
import traceback
from fastrunner import models
from rest_framework.response import Response

def get_para(keyword,text):
    """get para.

    """
    content = json.loads(text.lower())
    key = content["data"].get(keyword.lower().strip(), "")
    return key


def add_global_variable(extracts, id, content):
    project = models.Project.objects.get(id=id)
    for ext in extracts:
        try:
            for k, v in ext.items():
                val = get_para(k, content)
                _, tag = models.Variables.objects.update_or_create(project=project, key=k, defaults={"value": val if bool(val) else v})
        except Exception as e:
            traceback.print_exc()
            logging.error("添加参数为全局变量失败： {}".format(str(ext)))
            return Response({"traceback": str(e)}, "400")