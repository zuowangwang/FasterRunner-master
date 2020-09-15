#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from django.utils.decorators import method_decorator
from rest_framework.permissions import DjangoModelPermissions

from fastrunner import models, serializers
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response

from utils.decorator import request_log
from utils.permissions import IsBelongToProject
from fastrunner.utils import response


class HelperView(GenericViewSet):
    serializer_class = serializers.HelperSerializer
    permission_classes = (DjangoModelPermissions, IsBelongToProject)

    def get_queryset(self):
        queryset = models.Helper.objects.filter(is_show=True)
        return queryset

    @method_decorator(request_log(level='INFO'))
    def single(self, request, **kwargs):
        """
        查询当前展示的帮助信息
        """
        try:
            helper = self.get_queryset().get(id=kwargs['pk'])
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
            helper = models.Helper.objects
            title = request.data.get('title', '') or helper.get(id=pk).title
            txt = request.data.get('content', '') or helper.get(id=pk).content
            helper.filter(id=pk).update(title=title, content=txt, is_show=True)
            return self.single(request, **kwargs)
        except:
            return Response(response.HELPER_UPDATE_ERROR)
