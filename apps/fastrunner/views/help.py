#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import permission_classes

from fastrunner import models, serializers
from fastrunner.utils import response
from fastrunner.utils.decorator import request_log
from fastrunner.utils.permissions import IsBelongToProject, OnlyAllowSuperUser


class HelperView(GenericViewSet):
    serializer_class = serializers.HelperSerializer
    permission_classes = (DjangoModelPermissions, IsBelongToProject, OnlyAllowSuperUser)
    queryset = models.Helper.objects

    @method_decorator(request_log(level='INFO'))
    def single(self, request, **kwargs):
        """
        查询当前展示的帮助信息
        """
        try:
            helper = self.queryset.get(id=kwargs['pk'])
        except:
            return Response(response.HELPER_NOT_EXISTS)

        help_manual = {
            "title": helper.title,
            "content": helper.content
        }

        return Response(help_manual)


    @method_decorator(request_log(level='INFO'))
    def update(self, request, **kwargs):
        """更新指定的文档
        pk: int
        """
        pk = kwargs['pk']
        try:
            title = request.data.get('title', '') or self.queryset.get(id=pk).title
            txt = request.data.get('content', '') or self.queryset.get(id=pk).content
            is_show = request.data.get('is_show') or self.queryset.get(id=pk).is_show
            self.queryset.filter(id=pk).update(title=title, content=txt, is_show=is_show)
            return Response(response.HELPER_UPDATE_SUCCESS)
        except:
            return Response(response.HELPER_UPDATE_ERROR)

    @method_decorator(request_log(level='INFO'))
    def add(self, request):
        """增加文档

        """
        title = request.data.get('title', '')
        txt = request.data.get('content', '')
        is_show = request.data.get('is_show') or True
        try:
            self.queryset.get_or_create(title=title, content=txt, is_show=is_show)
            return Response(response.HELPER_ADD_SUCCESS)
        except:
            return Response(response.HELPER_ADD_ERROR)

    @method_decorator(request_log(level='INFO'))
    def list(self, request):
        """查询所有文档

        """
        is_show = request.query_params.get("show")
        try:
            if is_show == "1":
                return Response(self.queryset.filter(is_show=True).values())
            elif is_show == "0":
                return Response(self.queryset.filter(is_show=False).values())
            else:
                return Response(self.queryset.values())
        except Exception as e:
            print(str(e))
            return Response(response.HELPS_NOT_EXISTS)

    @method_decorator(request_log(level='INFO'))
    def delete(self, request, **kwargs):
        """
        删除一个文档： pk
        删除多个
        [{
            id:int
        }]
        """

        try:
            if kwargs.get('pk'):  # 单个删除
                models.Helper.objects.get(id=kwargs['pk']).delete()
            else:
                for nums in request.data:
                    models.Helper.objects.get(id=nums['id']).delete()

        except ObjectDoesNotExist:
            return Response(response.HELPER_NOT_EXISTS)

        return Response(response.HELPER_DEL_SUCCESS)