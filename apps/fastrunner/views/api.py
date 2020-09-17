from django.db import DataError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.permissions import DjangoModelPermissions

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
            queryset = queryset.filter(name__contains=search)

        if node != '':
            queryset = queryset.filter(relation=node)

        pagination_queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer(pagination_queryset, many=True)

        return self.get_paginated_response(serializer.data)

    @method_decorator(request_log(level='INFO'))
    def add(self, request):
        """
        新增一个接口
        """
        apis = []
        if request.data.get("bulk_add"):
            project_id = int(request.data.get("project"))
            node_id = int(request.data.get("nodeId"))
            temps = request.data.get("interfaces", {})
            for temp in temps.values():
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
                apis.append(models.API(**api_body))
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
            apis.append(models.API(**api_body))
        try:
            models.API.objects.bulk_create(apis)
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
