# _*_ coding: utf-8 _*_
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import DjangoModelPermissions
from djcelery.models import TaskMeta

from FasterRunner import pagination
from fastrunner.serializers import TaskMetaSerializer


class TaskMetaView(GenericViewSet, mixins.ListModelMixin):
    """
    展示当天异步任务执行结果
    """
    pagination_class = pagination.MyPageNumberPagination
    permission_classes = (DjangoModelPermissions,)
    queryset = TaskMeta.objects.all().order_by('-date_done')
    serializer_class = TaskMetaSerializer
