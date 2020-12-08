from django.core.exceptions import ObjectDoesNotExist
from django.db import DataError
from django.db.models import Q
from django.utils.decorators import method_decorator
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from fastrunner import models, serializers
from fastrunner.utils import response
from fastrunner.utils.decorator import request_log
from fastrunner.utils.parser import Format, Parse
from fastrunner.utils.permissions import IsBelongToProject
from fastrunner.utils.prepare import api_end


class APITemplateView(GenericViewSet):
    """
    API操作视图
    """
    serializer_class = serializers.APISerializer
    queryset = models.API.objects
    permission_classes = (DjangoModelPermissions, IsBelongToProject)

    @method_decorator(request_log(level='DEBUG'))
    def list(self, request):
        """
        接口列表 {
            project: int,
            node: int
        }
        """

        node = request.query_params["node"]
        project = request.query_params["project"]
        search = request.query_params["search"]
        queryset = self.get_queryset().filter(project__id=project).order_by('-update_time')

        if search != '':
            queryset = queryset.filter(Q(name__contains=search) | Q(url__contains=search))

        if node != '':
            queryset = queryset.filter(relation=node)

        pagination_queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer(pagination_queryset, many=True)

        return self.get_paginated_response(serializer.data)

    @method_decorator(request_log(level='INFO'))
    def add(self, request):
        """添加或更新一个或多个接口

        """
        add_apis = []
        if request.data.get("bulk_add"):
            project_id = int(request.data.get("project"))
            node_id = int(request.data.get("nodeId"))
            temps = request.data.get("interfaces", {})
            for temp in temps.values():
                id = temp.get('id', 0)
                temp.update({
                    "project": project_id,
                    "nodeId": node_id
                })
                api = Format(temp)
                api.parse()

                api_body = {
                    'name': api.name,
                    'body': api.testcase,
                    'url': api.url,
                    'method': api.method,
                    'project': models.Project.objects.get(id=api.project),
                    'relation': api.relation
                }
                obj = models.API.objects.filter(id=id, relation=node_id, project=project_id)
                if obj:
                    obj.update(**api_body)
                else:
                    add_apis.append(models.API(**api_body))
        else:
            api = Format(request.data)
            api.parse()

            api_body = {
                'name': api.name,
                'body': api.testcase,
                'url': api.url,
                'method': api.method,
                'project': models.Project.objects.get(id=api.project),
                'relation': api.relation
            }
            add_apis.append(models.API(**api_body))
        try:
            if len(add_apis):
                models.API.objects.bulk_create(add_apis)
        except DataError:
            return Response(response.DATA_TO_LONG)
        except Exception as e:
            return Response({"error": str(e)})

        return Response(response.API_ADD_SUCCESS)

    @method_decorator(request_log(level='INFO'))
    def update(self, request, **kwargs):
        """
        更新接口
        """
        pk = kwargs['pk']
        api = Format(request.data)
        api.parse()

        api_body = {
            'name': api.name,
            'body': api.testcase,
            'url': api.url,
            'method': api.method,
        }

        try:
            models.API.objects.filter(id=pk).update(**api_body)
        except ObjectDoesNotExist:
            return Response(response.API_NOT_FOUND)

        return Response(response.API_UPDATE_SUCCESS)

    @method_decorator(request_log(level='INFO'))
    def copy(self, request, **kwargs):
        """
        pk int: test id
        {
            name: api name
        }
        """
        pk = kwargs['pk']
        name = request.data['name']
        api = models.API.objects.get(id=pk)
        body = eval(api.body)
        body["name"] = name
        api.body = body
        api.id = None
        api.name = name
        api.save()
        return Response(response.API_ADD_SUCCESS)

    @method_decorator(request_log(level='INFO'))
    def move(self, request, **kwargs):
        """移动接口到新的node

        """
        relation_id = request.data.get('relation')
        ids = request.data.get('ids', [])
        success, failure = [], []
        for id in ids:
            try:
                api = models.API.objects.get(id=id)
                api.relation = int(relation_id)
                api.save()
                success.append(id)
            except:
                failure.append(id)
        result = {
            'relation': relation_id,
            "success": success,
            'failure': failure
        }
        ret = response.API_MOVE_SUCCESS
        ret.update(result=result)
        return Response(ret)


    @method_decorator(request_log(level='INFO'))
    def delete(self, request, **kwargs):
        """
        删除一个接口 pk
        删除多个
        [{
            id:int
        }]
        """

        try:
            if kwargs.get('pk'):  # 单个删除
                api_end(kwargs['pk'])
            else:
                for content in request.data:
                    api_end(content['id'])

        except ObjectDoesNotExist:
            return Response(response.API_NOT_FOUND)

        return Response(response.API_DEL_SUCCESS)

    @method_decorator(request_log(level='INFO'))
    def single(self, request, **kwargs):
        """
        查询单个api，返回body信息
        """
        try:
            api = models.API.objects.get(id=kwargs['pk'])
        except ObjectDoesNotExist:
            return Response(response.API_NOT_FOUND)

        parse = Parse(eval(api.body))
        parse.parse_http()

        resp = {
            'id': api.id,
            'body': parse.testcase,
            'success': True,
        }

        return Response(resp)
