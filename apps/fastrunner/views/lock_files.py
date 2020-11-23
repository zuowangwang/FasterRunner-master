# _*_ coding: utf-8 _*_
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import DjangoModelPermissions
from rest_framework import status
from rest_framework.response import Response

from fastrunner.serializers import LockFilesSerializer
from fastrunner.utils.permissions import IsBelongToProject
from fastrunner.models import LockFiles


class LockFilesView(GenericViewSet, mixins.CreateModelMixin):
    """
    锁定文件视图
    删除和创建时同样的请求参数
    """
    permission_classes = (DjangoModelPermissions, IsBelongToProject)
    serializer_class = LockFilesSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get("project", 0)
        lock_type = self.request.data.get("lock_type", 0)
        file_id = self.request.data.get("file_id", 0)
        return LockFiles.objects.filter(project_id=project_id, lock_type=lock_type, file_id=file_id)

    def create(self, request, *args, **kwargs):
        lock_queryset = self.get_queryset()
        if lock_queryset:
            lock_queryset.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
